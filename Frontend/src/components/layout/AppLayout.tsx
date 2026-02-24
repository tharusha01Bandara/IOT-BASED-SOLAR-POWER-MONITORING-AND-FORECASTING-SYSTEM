import { useState } from "react";
import { Outlet } from "react-router-dom";
import { AppSidebar } from "./AppSidebar";
import { TopBar } from "./TopBar";
import { SidebarProvider } from "@/components/ui/sidebar";
import { useSolarData } from "@/hooks/useSolarData";
import { SolarDataContext } from "@/contexts/SolarDataContext";

export function AppLayout() {
  const solarData = useSolarData();
  const [device] = useState("tracker01");

  return (
    <SolarDataContext.Provider value={solarData}>
      <SidebarProvider>
        <div className="min-h-screen flex w-full">
          <AppSidebar />
          <div className="flex-1 flex flex-col min-w-0">
            <TopBar device={device} />
            <main className="flex-1 p-4 md:p-6 overflow-auto">
              <Outlet />
            </main>
          </div>
        </div>
      </SidebarProvider>
    </SolarDataContext.Provider>
  );
}
