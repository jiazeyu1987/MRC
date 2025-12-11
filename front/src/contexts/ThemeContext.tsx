import React, { createContext, useContext, useState, ReactNode } from 'react';
import { ThemeKey, ThemeConfig, THEMES } from '../components/common/theme/themes';

interface ThemeContextValue {
  themeKey: ThemeKey;
  theme: ThemeConfig;
  setThemeKey: (k: ThemeKey) => void;
}

const ThemeContext = createContext<ThemeContextValue>({
  themeKey: 'blue',
  theme: THEMES.blue,
  setThemeKey: () => {}
});

interface ThemeProviderProps {
  children: ReactNode;
}

export const ThemeProvider: React.FC<ThemeProviderProps> = ({ children }) => {
  const [themeKey, setThemeKey] = useState<ThemeKey>('blue');
  const theme = THEMES[themeKey];

  return (
    <ThemeContext.Provider value={{ themeKey, theme, setThemeKey }}>
      {children}
    </ThemeContext.Provider>
  );
};

export { ThemeContext };
export const useTheme = () => useContext(ThemeContext);