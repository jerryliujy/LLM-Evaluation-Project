export const formatDate = (dateInput?: string | Date): string => {
  if (!dateInput) return "N/A";
  try {
    const date = new Date(dateInput);
    // Basic check for valid date
    if (isNaN(date.getTime())) return "Invalid Date";
    return date.toLocaleString(); // Or any other format you prefer
  } catch (e) {
    return "Invalid Date";
  }
};

/**
 * 格式化标签数组，处理不同格式的标签数据
 * @param value 标签数据，可以是数组、JSON字符串或逗号分隔的字符串
 * @returns 标签字符串数组
 */
export const formatTags = (value: any): string[] => {
  if (!value) return [];
  
  // 如果已经是数组，直接返回
  if (Array.isArray(value)) {
    return value.filter(tag => tag && typeof tag === 'string');
  }
  
  // 如果是字符串，尝试解析
  if (typeof value === 'string') {
    // 先尝试作为JSON解析
    try {
      const parsed = JSON.parse(value);
      if (Array.isArray(parsed)) {
        return parsed.filter(tag => tag && typeof tag === 'string');
      }
    } catch {
      // JSON解析失败，按逗号分割
      return value.split(',').map(tag => tag.trim()).filter(Boolean);
    }
  }
  
  return [];
};
