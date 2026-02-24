import { RefreshCw, Pause, Play, Monitor, Moon, Sun } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { SidebarTrigger } from "@/components/ui/sidebar";
import { useSolarContext } from "@/contexts/SolarDataContext";
import { useEffect, useState } from "react";

interface TopBarProps {
  device: string;
}

export function TopBar({ device }: TopBarProps) {
  const { isLive, setIsLive, lastUpdated, refresh, timeRange, setTimeRange } = useSolarContext();
  const [isDark, setIsDark] = useState(() => {
    if (typeof window !== "undefined") {
      return document.documentElement.classList.contains("dark") ||
        window.matchMedia("(prefers-color-scheme: dark)").matches;
    }
    return true;
  });

  useEffect(() => {
    document.documentElement.classList.toggle("dark", isDark);
  }, [isDark]);

  return (
    <header className="sticky top-0 z-30 flex items-center justify-between gap-3 border-b border-border bg-background/80 backdrop-blur-sm px-4 h-14">
      <div className="flex items-center gap-3">
        <SidebarTrigger className="lg:hidden" />
        <Select defaultValue={device}>
          <SelectTrigger className="w-[140px] h-8 text-xs">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="tracker01">🛰️ Tracker 01</SelectItem>
            <SelectItem value="tracker02">🛰️ Tracker 02</SelectItem>
          </SelectContent>
        </Select>

        <Select value={timeRange} onValueChange={(v) => setTimeRange(v as any)}>
          <SelectTrigger className="w-[90px] h-8 text-xs">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="15m">15 min</SelectItem>
            <SelectItem value="1h">1 hour</SelectItem>
            <SelectItem value="6h">6 hours</SelectItem>
            <SelectItem value="24h">24 hours</SelectItem>
          </SelectContent>
        </Select>
      </div>

      <div className="flex items-center gap-2">
        <div className="hidden sm:flex items-center gap-1.5 text-[11px] text-muted-foreground mr-2">
          <div className={`w-1.5 h-1.5 rounded-full ${isLive ? "bg-success animate-pulse" : "bg-offline"}`} />
          {isLive ? "Live" : "Paused"} · {lastUpdated.toLocaleTimeString()}
        </div>

        <Button variant="ghost" size="icon" className="h-8 w-8" onClick={() => setIsLive(!isLive)}>
          {isLive ? <Pause className="w-3.5 h-3.5" /> : <Play className="w-3.5 h-3.5" />}
        </Button>
        <Button variant="ghost" size="icon" className="h-8 w-8" onClick={refresh}>
          <RefreshCw className="w-3.5 h-3.5" />
        </Button>
        <Button variant="ghost" size="icon" className="h-8 w-8" onClick={() => setIsDark(!isDark)}>
          {isDark ? <Sun className="w-3.5 h-3.5" /> : <Moon className="w-3.5 h-3.5" />}
        </Button>
      </div>
    </header>
  );
}
