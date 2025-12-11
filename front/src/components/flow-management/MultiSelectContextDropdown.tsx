import React, { useState, useRef, useMemo, useEffect } from 'react';
import { ChevronDown } from 'lucide-react';
import { Role } from '../../types/role';

interface Option {
  value: string;
  label: string;
  type: 'system' | 'role';
}

interface MultiSelectContextDropdownProps {
  value: string | string[];
  onChange: (value: string | string[]) => void;
  roles: Role[];
  className?: string;
}

const MultiSelectContextDropdown: React.FC<MultiSelectContextDropdownProps> = ({
  value,
  onChange,
  roles,
  className = ""
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  // Convert value to array for handling (support both strings and JSON arrays)
  const selectedValues = useMemo(() => {
    if (Array.isArray(value)) {
      return value;
    }

    if (!value) {
      return [];
    }

    // Try to parse as JSON array (for multi-role selections)
    try {
      const parsed = JSON.parse(value);
      return Array.isArray(parsed) ? parsed : [value];
    } catch {
      // If not valid JSON, treat as single string value
      return [value];
    }
  }, [value]);

  // Options available
  const systemOptions: Option[] = [
    { value: '__TOPIC__', label: '预设议题', type: 'system' }
  ];

  const roleOptions: Option[] = roles.map(role => ({
    value: role.name,
    label: role.name,
    type: 'role'
  }));

  const allOptions: Option[] = [...systemOptions, ...roleOptions];

  const handleToggle = (optionValue: string) => {
    let newSelectedValues: string[];

    // All options are now multi-select
    if (selectedValues.includes(optionValue)) {
      newSelectedValues = selectedValues.filter(v => v !== optionValue);
    } else {
      newSelectedValues = [...selectedValues, optionValue];
    }

    // Convert to appropriate format for backend
    let result: string | string[];
    if (newSelectedValues.length === 0) {
      result = '';
    } else if (newSelectedValues.length === 1) {
      // Single option remains as single string
      result = newSelectedValues[0];
    } else {
      // Multiple options get serialized as JSON array for backend
      result = JSON.stringify(newSelectedValues);
    }

    onChange(result);
  };

  const handleRemove = (optionValue: string) => {
    handleToggle(optionValue);
  };

  const getDisplayText = () => {
    if (selectedValues.length === 0) return '选择上下文策略';

    if (selectedValues.length === 1) {
      const option = allOptions.find(o => o.value === selectedValues[0]);
      return option ? option.label : selectedValues[0];
    }

    return `已选择 ${selectedValues.length} 项`;
  };

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  return (
    <div className="relative" ref={dropdownRef}>
      <div
        className={`w-full border rounded px-2 py-1 text-sm cursor-pointer min-h-[32px] flex items-center justify-between ${className}`}
        onClick={() => setIsOpen(!isOpen)}
      >
        <span className="truncate">{getDisplayText()}</span>
        <ChevronDown size={16} className={`transition-transform ${isOpen ? 'rotate-180' : ''}`} />
      </div>

      {isOpen && (
        <div className="absolute z-10 w-full mt-1 bg-white border rounded shadow-lg max-h-60 overflow-auto">
          {allOptions.map((option) => (
            <div
              key={option.value}
              className="flex items-center px-3 py-2 hover:bg-gray-50 cursor-pointer"
              onClick={() => handleToggle(option.value)}
            >
              <input
                type="checkbox"
                checked={selectedValues.includes(option.value)}
                onChange={() => {}}
                className="mr-2"
              />
              <span className="text-sm">{option.label}</span>
              {option.type === 'role' && (
                <span className="ml-2 text-xs text-gray-400">(角色)</span>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Selected items display */}
      {selectedValues.length > 1 && (
        <div className="flex flex-wrap gap-1 mt-2">
          {selectedValues.map((selectedValue) => {
            const option = allOptions.find(o => o.value === selectedValue);
            return (
              <span
                key={selectedValue}
                className="inline-flex items-center gap-1 px-2 py-1 text-xs bg-blue-100 text-blue-800 rounded"
              >
                {option ? option.label : selectedValue}
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    handleRemove(selectedValue);
                  }}
                  className="hover:text-blue-600"
                >
                  ×
                </button>
              </span>
            );
          })}
        </div>
      )}
    </div>
  );
};

export default MultiSelectContextDropdown;