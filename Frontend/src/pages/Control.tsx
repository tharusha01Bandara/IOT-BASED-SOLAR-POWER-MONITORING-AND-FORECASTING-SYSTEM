import { Fan, Info } from "lucide-react";
import { useSolarContext } from "@/contexts/SolarDataContext";
import { Switch } from "@/components/ui/switch";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";

export default function Control() {
  const { fanEvents, currentReading } = useSolarContext();

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      <div>
        <h1 className="text-xl md:text-2xl font-bold">Control & Events</h1>
        <p className="text-sm text-muted-foreground mt-0.5">Fan control and event history</p>
      </div>

      <div className="grid md:grid-cols-2 gap-4">
        {/* Cooling Logic */}
        <div className="glass-card rounded-xl p-4 animate-fade-in">
          <div className="flex items-center gap-2 mb-3">
            <Info className="w-4 h-4 text-info" />
            <h3 className="text-sm font-semibold">Cooling Logic</h3>
          </div>
          <div className="space-y-2 text-sm">
            <div className="flex justify-between p-2 rounded-lg bg-muted/50">
              <span className="text-muted-foreground">Fan ON threshold</span>
              <span className="font-mono font-medium">&gt; 40°C</span>
            </div>
            <div className="flex justify-between p-2 rounded-lg bg-muted/50">
              <span className="text-muted-foreground">Fan OFF threshold</span>
              <span className="font-mono font-medium">&lt; 38°C</span>
            </div>
            <div className="flex justify-between p-2 rounded-lg bg-muted/50">
              <span className="text-muted-foreground">Current temp</span>
              <span className="font-mono font-medium">{currentReading.temperature}°C</span>
            </div>
            <div className="flex justify-between p-2 rounded-lg bg-muted/50">
              <span className="text-muted-foreground">Fan status</span>
              <span className={`font-mono font-medium ${currentReading.fan_status ? "text-warning" : "text-success"}`}>
                {currentReading.fan_status ? "ON" : "OFF"}
              </span>
            </div>
          </div>
        </div>

        {/* Manual Override (disabled) */}
        <div className="glass-card rounded-xl p-4 animate-fade-in opacity-60">
          <div className="flex items-center gap-2 mb-3">
            <Fan className="w-4 h-4" />
            <h3 className="text-sm font-semibold">Manual Override</h3>
            <span className="text-[10px] bg-muted px-2 py-0.5 rounded-full text-muted-foreground">Coming Soon</span>
          </div>
          <div className="flex items-center justify-between p-3 rounded-lg bg-muted/30">
            <span className="text-sm text-muted-foreground">Force Fan ON</span>
            <Switch disabled />
          </div>
          <p className="text-[11px] text-muted-foreground mt-2">Manual override is disabled. Contact admin to enable.</p>
        </div>
      </div>

      {/* Fan Timeline */}
      <div className="glass-card rounded-xl p-4 animate-fade-in">
        <h3 className="text-sm font-semibold mb-3">Fan Events Timeline</h3>
        <div className="flex gap-1 h-8 mb-4 rounded overflow-hidden">
          {fanEvents.map((ev, i) => (
            <div
              key={i}
              className={`flex-1 ${ev.event_type === "fan_on" ? "bg-warning/60" : "bg-success/30"}`}
              title={`${ev.event_type} at ${new Date(ev.timestamp).toLocaleTimeString()} — ${ev.reason}`}
            />
          ))}
        </div>
        <div className="flex gap-4 text-[11px] text-muted-foreground">
          <div className="flex items-center gap-1.5"><div className="w-3 h-3 rounded bg-warning/60" /> Fan ON</div>
          <div className="flex items-center gap-1.5"><div className="w-3 h-3 rounded bg-success/30" /> Fan OFF</div>
        </div>
      </div>

      {/* Event Log */}
      <div className="glass-card rounded-xl p-4 animate-fade-in">
        <h3 className="text-sm font-semibold mb-3">Event Log</h3>
        <div className="overflow-auto max-h-80">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead className="text-xs">Timestamp</TableHead>
                <TableHead className="text-xs">Event</TableHead>
                <TableHead className="text-xs">Reason</TableHead>
                <TableHead className="text-xs text-right">Temp (°C)</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {fanEvents.map((ev, i) => (
                <TableRow key={i}>
                  <TableCell className="text-xs font-mono">{new Date(ev.timestamp).toLocaleTimeString()}</TableCell>
                  <TableCell>
                    <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${ev.event_type === "fan_on" ? "bg-warning/10 text-warning" : "bg-success/10 text-success"}`}>
                      {ev.event_type === "fan_on" ? "Fan ON" : "Fan OFF"}
                    </span>
                  </TableCell>
                  <TableCell className="text-xs text-muted-foreground">{ev.reason}</TableCell>
                  <TableCell className="text-xs font-mono text-right">{ev.value}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      </div>
    </div>
  );
}
