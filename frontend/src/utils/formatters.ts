export const formatDate = (dateInput?: string | Date): string => {
    if (!dateInput) return 'N/A';
    try {
        const date = new Date(dateInput);
        // Basic check for valid date
        if (isNaN(date.getTime())) return 'Invalid Date';
        return date.toLocaleString(); // Or any other format you prefer
    } catch (e) {
        return 'Invalid Date';
    }
};