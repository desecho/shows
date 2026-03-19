import axios from "axios";
import { ref, type Ref } from "vue";

import type { RecordType, SortData } from "../types";

import { listWatchedId, listWatchingId } from "../const";
import { getUrl } from "../helpers";
import { $toast } from "../toast";

import { useApiCall } from "./useAsyncOperation";

export function useShowOperations(): {
    addingToList: Ref<Record<string, boolean>>;
    addToList: (showId: number, listId: number, record?: RecordType) => void;
    addToMyList: (
        showId: number,
        listId: number,
        records: RecordType[],
        myRecords: RecordType[],
        isLoggedIn: boolean,
    ) => void;
    removeRecord: (record: RecordType, records: RecordType[]) => void;
    changeRating: (record: RecordType, rating: number) => void;
    saveComment: (record: RecordType) => void;
    showCommentArea: (record: RecordType) => void;
    updateRecordComment: (record: RecordType, comment: string) => void;
    saveRecordsOrder: (records: RecordType[]) => void;
    moveToTop: (record: RecordType, records: RecordType[]) => void;
    moveToBottom: (record: RecordType, records: RecordType[]) => void;
} {
    // Track loading state for add to list buttons
    const addingToList = ref<Record<string, boolean>>({});

    // Error handling composables
    const addToListOperation = useApiCall("Add Show to List");
    const removeRecordOperation = useApiCall("Remove Show from List");
    const updateRecordOperation = useApiCall("Update Show Record");

    /**
     * Add show to a list
     */
    async function addToList(
        showId: number,
        listId: number,
        record?: RecordType,
    ): Promise<void> {
        const result = await addToListOperation.execute(async () => {
            const response = await axios.post(
                getUrl(`add-to-list/${showId}/`),
                { listId },
            );
            return response.data as Record<string, unknown>;
        });

        if (result.success) {
            if (record !== undefined) {
                record.listId = listId;
                record.additionDate = Date.now();
            }
        }
    }

    /**
     * Add show to user's own list (when viewing profile)
     */
    async function addToMyList(
        showId: number,
        listId: number,
        records: RecordType[],
        myRecords: RecordType[],
        isLoggedIn: boolean,
    ): Promise<void> {
        if (!isLoggedIn) {
            $toast.error("You must be logged in to add shows to your list");
            return;
        }

        const loadingKey = `${showId}-${listId}`;
        addingToList.value[loadingKey] = true;

        try {
            // Add to myRecords for immediate UI update
            const showData = records.find(
                (record) => record.show.id === showId,
            )?.show;
            await addToList(showId, listId); // Call the existing addToList function

            if (showData) {
                const newRecord: RecordType = {
                    id: Date.now(),
                    show: showData,
                    listId,
                    rating: 0,
                    comment: "",
                    additionDate: Date.now(),
                    order: myRecords.length + 1,
                    providerRecords: [],
                    ratingOriginal: 0,
                    commentArea: false,
                };
                myRecords.push(newRecord);
            }

            let listName: string;
            if (listId === listWatchedId) {
                listName = "Watched";
            } else if (listId === listWatchingId) {
                listName = "Watching";
            } else {
                listName = "To Watch";
            }
            $toast.success(`Show added to your ${listName} list`);
        } catch (error) {
            console.log("Error adding show to list:", error);
            $toast.error("Error adding show to your list");
        } finally {
            addingToList.value[loadingKey] = false;
        }
    }

    /**
     * Remove record from list
     */
    async function removeRecord(
        record: RecordType,
        records: RecordType[],
    ): Promise<void> {
        // Optimistically remove from UI first
        const actualIndex = records.findIndex((r) => r.id === record.id);
        if (actualIndex !== -1) {
            records.splice(actualIndex, 1);
        }

        const result = await removeRecordOperation.execute(async () => {
            const response = await axios.delete(
                getUrl(`remove-record/${record.id}/`),
            );
            return response.data as Record<string, unknown>;
        });

        if (result.success) {
            $toast.success("Show removed from your list!");
        } else if (actualIndex !== -1) {
            // Restore the record if deletion fails
            records.splice(actualIndex, 0, record);
        }
    }

    /**
     * Change show rating
     */
    async function changeRating(
        record: RecordType,
        rating: number,
    ): Promise<void> {
        // Store the original rating before the change
        const originalRating = record.rating;

        // Optimistically update the rating
        record.rating = rating;

        const result = await updateRecordOperation.execute(async () => {
            const response = await axios.put(
                getUrl(`change-rating/${record.id}/`),
                { rating },
            );
            return response.data as Record<string, unknown>;
        });

        if (result.success) {
            // Update the original rating to the new confirmed value
            // eslint-disable-next-line require-atomic-updates
            record.ratingOriginal = rating;
            $toast.success(`Rating updated to ${rating} stars!`);
        } else {
            // Revert to the original rating if the save fails
            // eslint-disable-next-line require-atomic-updates
            record.rating = originalRating;
        }
    }

    /**
     * Save comment
     */
    function saveComment(record: RecordType): void {
        const data = {
            comment: record.comment,
        };

        axios
            .put(getUrl(`save-comment/${record.id}/`), data)
            .then(() => {
                if (record.comment === "") {
                    record.commentArea = false;
                }
            })
            .catch(() => {
                $toast.error("Error saving a comment");
            });
    }

    /**
     * Show comment area
     */
    function showCommentArea(record: RecordType): void {
        record.commentArea = true;
    }

    /**
     * Update record comment from child component
     */
    function updateRecordComment(record: RecordType, comment: string): void {
        record.comment = comment;
    }

    /**
     * Save records order
     */
    function saveRecordsOrder(records: RecordType[]): void {
        function getSortData(): SortData[] {
            const data: SortData[] = [];
            records.forEach((record) => {
                // Use the record's already-set order value, not the array index
                const sortData = { id: record.id, order: record.order };
                data.push(sortData);
            });
            return data;
        }

        const sortData = getSortData();

        axios
            .put(getUrl("save-records-order/"), { records: sortData })
            .then(() => {
                // Order saved successfully
            })
            .catch((error) => {
                console.error("Error saving show order:", error);
                $toast.error("Error saving show order");
            });
    }

    /**
     * Move record to top
     */
    function moveToTop(record: RecordType, records: RecordType[]): void {
        const actualIndex = records.findIndex((r) => r.id === record.id);
        if (actualIndex !== -1) {
            records.splice(actualIndex, 1);
            records.unshift(record);
            saveRecordsOrder(records);
        }
    }

    /**
     * Move record to bottom
     */
    function moveToBottom(record: RecordType, records: RecordType[]): void {
        const actualIndex = records.findIndex((r) => r.id === record.id);
        if (actualIndex !== -1) {
            records.splice(actualIndex, 1);
            records.push(record);
            saveRecordsOrder(records);
        }
    }

    return {
        // State
        addingToList,

        // Methods
        addToList: (
            showId: number,
            listId: number,
            record?: RecordType,
        ): void => {
            void addToList(showId, listId, record);
        },
        addToMyList: (
            showId: number,
            listId: number,
            records: RecordType[],
            myRecords: RecordType[],
            isLoggedIn: boolean,
        ): void => {
            void addToMyList(showId, listId, records, myRecords, isLoggedIn);
        },
        removeRecord: (record: RecordType, records: RecordType[]): void => {
            void removeRecord(record, records);
        },
        changeRating: (record: RecordType, rating: number): void => {
            void changeRating(record, rating);
        },
        saveComment,
        showCommentArea,
        updateRecordComment,
        saveRecordsOrder,
        moveToTop,
        moveToBottom,
    };
}
