import {
  Zap, TrendingUp, Sun, Thermometer, Droplets, Fan, Gauge,
} from "lucide-react";
import { KPICard } from "@/components/dashboard/KPICard";
import { AlertsPanel } from "@/components/dashboard/AlertsPanel";
import { ServoGauge } from "@/components/dashboard/ServoGauge";
import { useSolarContext } from "@/contexts/SolarDataContext";
import { StatusColor } from "@/types/solar";
import { Skeleton } from "@/components/ui/skeleton";

function getStatus(value: number, warn: number, crit: number, inverse = false): StatusColor {
  if (inverse) return value < crit ? "critical" : value < warn ? "warning" : "normal";
  return value > crit ? "critical" : value > warn ? "warning" : "normal";
}

export default function Overview() {
  const { currentReading, prediction, alerts, historicalData } = useSolarContext();
  
  if (!currentReading) {
    return (
      <div className="space-y-6 max-w-7xl mx-auto">
        <h1 className="text-xl md:text-2xl font-bold">Dashboard Overview</h1>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 md:gap-4">
          {[...Array(8)].map((_, i) => <Skeleton key={i} className="h-32 w-full" />)}
        </div>
      </div>
    );
  }

  const r = currentReading;
  const p = prediction || { predicted_power_15min: 0, confidence: 0 };
  const hData = historicalData || [];

  const sparkPower = hData.slice(-20).map((d) => d.power);
  const sparkLux = hData.slice(-20).map((d) => d.lux);
  const sparkTemp = hData.slice(-20).map((d) => d.temperature);
  const sparkHumidity = hData.slice(-20).map((d) => d.humidity);

  const fanIsOn = r.fan_status === "on" || r.fan_status === "ON" || r.fan_status === true;

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      <div>
        <h1 className="text-xl md:text-2xl font-bold">Dashboard Overview</h1>
        <p className="text-sm text-muted-foreground mt-0.5">Real-time solar tracker monitoring</p>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 md:gap-4">
        <KPICard
          title="Power" value={r.power || 0} unit="W"
          icon={<Zap className="w-4 h-4" />}
          status={getStatus(r.power || 0, 100, 80, true)}
          sparklineData={sparkPower}
        />
        <KPICard
          title="Predicted" value={p.predicted_power_15min} unit="W (+15m)"
          icon={<TrendingUp className="w-4 h-4" />}
          status="normal"
          subtitle={`${Math.round((p.confidence || 0) * 100)}% conf`}
          sparklineColor="hsl(265, 60%, 60%)"
        />
        <KPICard
          title="Lux" value={Math.round(r.lux || 0).toLocaleString()} unit="lx"
          icon={<Sun className="w-4 h-4" />}
          status={getStatus(r.lux || 0, 35000, 20000, true)}
          sparklineData={sparkLux}
          sparklineColor="hsl(45, 95%, 55%)"
        />
        <KPICard
          title="Temperature" value={r.temperature || 0} unit="�C"
          icon={<Thermometer className="w-4 h-4" />}
          status={getStatus(r.temperature || 0, 42, 46)}
          sparklineData={sparkTemp}
          sparklineColor="hsl(0, 72%, 55%)"
        />
        <KPICard
          title="Humidity" value={r.humidity || 0} unit="%"
          icon={<Droplets className="w-4 h-4" />}
          status="normal"
          sparklineData={sparkHumidity}
          sparklineColor="hsl(200, 80%, 55%)"
        />
        <KPICard
          title="Fan" value={fanIsOn ? "ON" : "OFF"} unit=""
          icon={<Fan className={`w-4 h-4 ${fanIsOn ? "animate-spin text-blue-500" : ""}`} />}
          status={fanIsOn ? "warning" : "normal"}
          subtitle={fanIsOn ? "Cooling active" : "Idle"}
        />
        <KPICard
          title="Confidence" value={`${Math.round((p.confidence || 0) * 100)}%`} unit=""
          icon={<Gauge className="w-4 h-4" />}
          status={(p.confidence || 0) > 0.9 ? "normal" : (p.confidence || 0) > 0.8 ? "warning" : "critical"}
        />
        <ServoGauge angle={r.servo_angle || 0} ldrLeft={r.ldr_left} ldrRight={r.ldr_right} />
      </div>

      <AlertsPanel alerts={alerts || []} />
    </div>
  );
}
