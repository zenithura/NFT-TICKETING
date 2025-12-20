/**
 * Web Worker for off-main-thread event filtering and sorting.
 * Prevents UI blocking (INP) when dealing with large datasets.
 */

/* eslint-disable no-restricted-globals */
self.onmessage = (e: MessageEvent) => {
    const { events, filter, category } = e.data;

    if (!events) {
        self.postMessage([]);
        return;
    }

    const searchLower = filter.toLowerCase();

    const filtered = events.filter((e: any) => {
        const matchesSearch = e.title.toLowerCase().includes(searchLower) ||
            e.description.toLowerCase().includes(searchLower) ||
            e.category.toLowerCase().includes(searchLower);

        const matchesCategory = category === 'All' || e.category === category;

        return matchesSearch && matchesCategory;
    });

    self.postMessage(filtered);
};

export { };
