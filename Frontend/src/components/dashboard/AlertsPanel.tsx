import { AlertTriangle, Thermometer, Sun, Wifi } from "lucide-react";
import { Alert } from "@/types/solar";

interface AlertsPanelProps {
  alerts: Alert[];
}

const alertIcons = {
  low_lux: Sun,
  overheat: Thermometer,
  power_drop: AlertTriangle,
  sensor_invalid: Wifi,
};

const severityStyles = {
  warning: "border-warning/30 bg-warning/5 text-warning",
  critical: "border-destructive/30 bg-destructive/5 text-destructive",
  info: "border-info/30 bg-info/5 text-info",
};

export function AlertsPanel({ alerts }: AlertsPanelProps) {
  if (alerts.length === 0) {
    return (
      <div className="glass-card rounded-xl p-4 animate-fade-in">
        <h3 className="text-sm font-semibold mb-3">Alerts</h3>
        <div className="text-xs text-muted-foreground text-center py-4">✅ All systems normal</div>
      </div>
    );
  }

  return (
    <div className="glass-card rounded-xl p-4 animate-fade-in">
      <h3 className="text-sm font-semibold mb-3">
        Alerts <span className="text-xs font-normal text-muted-foreground ml-1">({alerts.length})</span>
      </h3>
      <div className="space-y-2 max-h-48 overflow-y-auto">
        {alerts.map((alert) => {
          const Icon = alertIcons[alert.type];
          return (
            <div key={alert.id} className={`flex items-start gap-2 p-2.5 rounded-lg border text-xs ${severityStyles[alert.severity]}`}>
              <Icon className="w-3.5 h-3.5 mt-0.5 flex-shrink-0" />
              <div className="flex-1">
                <p className="font-medium">{alert.message}</p>
                <p className="text-muted-foreground mt-0.5">{new Date(alert.timestamp).toLocaleTimeString()}</p>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
