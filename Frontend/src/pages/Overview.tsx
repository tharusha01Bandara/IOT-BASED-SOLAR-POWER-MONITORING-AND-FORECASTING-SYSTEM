import {
  Zap, TrendingUp, Sun, Thermometer, Droplets, Fan, Gauge,
} from "lucide-react";
import { KPICard } from "@/components/dashboard/KPICard";
import { AlertsPanel } from "@/components/dashboard/AlertsPanel";
import { ServoGauge } from "@/components/dashboard/ServoGauge";
import { useSolarContext } from "@/contexts/SolarDataContext";
import { StatusColor } from "@/types/solar";

function getStatus(value: number, warn: number, crit: number, inverse = false): StatusColor {
  if (inverse) return value < crit ? "critical" : value < warn ? "warning" : "normal";
  return value > crit ? "critical" : value > warn ? "warning" : "normal";
}

export default function Overview() {
  const { currentReading, prediction, alerts, historicalData } = useSolarContext();
  const r = currentReading;

  const sparkPower = historicalData.slice(-20).map((d) => d.power);
  const sparkLux = historicalData.slice(-20).map((d) => d.lux);
  const sparkTemp = historicalData.slice(-20).map((d) => d.temperature);
  const sparkHumidity = historicalData.slice(-20).map((d) => d.humidity);

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      <div>
        <h1 className="text-xl md:text-2xl font-bold">Dashboard Overview</h1>
        <p className="text-sm text-muted-foreground mt-0.5">Real-time solar tracker monitoring</p>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 md:gap-4">
        <KPICard
          title="Power" value={r.power} unit="W"
          icon={<Zap className="w-4 h-4" />}
          status={getStatus(r.power, 100, 80, true)}
          sparklineData={sparkPower}
        />
        <KPICard
          title="Predicted" value={prediction.predicted_power_15min} unit="W (+15m)"
          icon={<TrendingUp className="w-4 h-4" />}
          status="normal"
          subtitle={`${Math.round(prediction.confidence * 100)}% conf`}
          sparklineColor="hsl(265, 60%, 60%)"
        />
        <KPICard
          title="Lux" value={Math.round(r.lux).toLocaleString()} unit="lx"
          icon={<Sun className="w-4 h-4" />}
          status={getStatus(r.lux, 35000, 20000, true)}
          sparklineData={sparkLux}
          sparklineColor="hsl(45, 95%, 55%)"
        />
        <KPICard
          title="Temperature" value={r.temperature} unit="°C"
          icon={<Thermometer className="w-4 h-4" />}
          status={getStatus(r.temperature, 42, 46)}
          sparklineData={sparkTemp}
          sparklineColor="hsl(0, 72%, 55%)"
        />
        <KPICard
          title="Humidity" value={r.humidity} unit="%"
          icon={<Droplets className="w-4 h-4" />}
          status="normal"
          sparklineData={sparkHumidity}
          sparklineColor="hsl(200, 80%, 55%)"
        />
        <KPICard
          title="Fan" value={r.fan_status ? "ON" : "OFF"} unit=""
          icon={<Fan className={`w-4 h-4 ${r.fan_status ? "animate-spin" : ""}`} />}
          status={r.fan_status ? "warning" : "normal"}
          subtitle={r.fan_status ? "Cooling active" : "Idle"}
        />
        <KPICard
          title="Confidence" value={`${Math.round(prediction.confidence * 100)}%`} unit=""
          icon={<Gauge className="w-4 h-4" />}
          status={prediction.confidence > 0.9 ? "normal" : prediction.confidence > 0.8 ? "warning" : "critical"}
        />
        <ServoGauge angle={r.servo_angle} />
      </div>

      <AlertsPanel alerts={alerts} />
    </div>
  );
}
