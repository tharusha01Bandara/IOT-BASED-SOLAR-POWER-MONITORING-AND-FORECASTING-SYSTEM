import { createContext, useContext } from "react";
import { useSolarData } from "@/hooks/useSolarData";

type SolarDataContextType = ReturnType<typeof useSolarData>;

export const SolarDataContext = createContext<SolarDataContextType | null>(null);

export function useSolarContext() {
  const ctx = useContext(SolarDataContext);
  if (!ctx) throw new Error("useSolarContext must be used within SolarDataContext.Provider");
  return ctx;
}
