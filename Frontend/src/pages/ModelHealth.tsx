import { Brain, Activity, Database, Wifi } from "lucide-react";
import { useSolarContext } from "@/contexts/SolarDataContext";
import { Progress } from "@/components/ui/progress";

export default function ModelHealth() {
  const { modelStatus, dataHealth } = useSolarContext();

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      <div>
        <h1 className="text-xl md:text-2xl font-bold">Model & Data Health</h1>
        <p className="text-sm text-muted-foreground mt-0.5">ML model status and data quality</p>
      </div>

      <div className="grid md:grid-cols-2 gap-4">
        {/* Model Status */}
        <div className="glass-card rounded-xl p-5 animate-fade-in">
          <div className="flex items-center gap-2 mb-4">
            <Brain className="w-5 h-5 text-primary" />
            <h3 className="font-semibold">Model Status</h3>
          </div>
          <div className="space-y-3">
            <div className="flex justify-between items-center">
              <span className="text-sm text-muted-foreground">Status</span>
              <span className={`text-sm font-medium px-2.5 py-0.5 rounded-full ${
                modelStatus.status === "trained" ? "bg-success/10 text-success" :
                modelStatus.status === "training" ? "bg-warning/10 text-warning" :
                "bg-destructive/10 text-destructive"
              }`}>
                {modelStatus.status === "trained" ? "✓ Trained" : modelStatus.status === "training" ? "⏳ Training" : "✗ Not Trained"}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-sm text-muted-foreground">Version</span>
              <span className="text-sm font-mono">{modelStatus.model_version}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-sm text-muted-foreground">Last Retrain</span>
              <span className="text-sm font-mono">{new Date(modelStatus.last_trained_time).toLocaleString()}</span>
            </div>
          </div>
        </div>

        {/* Model Metrics */}
        <div className="glass-card rounded-xl p-5 animate-fade-in">
          <div className="flex items-center gap-2 mb-4">
            <Activity className="w-5 h-5 text-primary" />
            <h3 className="font-semibold">Model Accuracy</h3>
          </div>
          <div className="space-y-4">
            <div>
              <div className="flex justify-between text-sm mb-1.5">
                <span className="text-muted-foreground">MAE</span>
                <span className="font-mono font-medium">{modelStatus.mae.toFixed(2)} W</span>
              </div>
              <Progress value={Math.max(0, 100 - modelStatus.mae * 5)} className="h-2" />
            </div>
            <div>
              <div className="flex justify-between text-sm mb-1.5">
                <span className="text-muted-foreground">RMSE</span>
                <span className="font-mono font-medium">{modelStatus.rmse.toFixed(2)} W</span>
              </div>
              <Progress value={Math.max(0, 100 - modelStatus.rmse * 4)} className="h-2" />
            </div>
          </div>
        </div>

        {/* Data Quality */}
        <div className="glass-card rounded-xl p-5 animate-fade-in">
          <div className="flex items-center gap-2 mb-4">
            <Database className="w-5 h-5 text-primary" />
            <h3 className="font-semibold">Data Quality</h3>
          </div>
          <div className="space-y-3">
            <div>
              <div className="flex justify-between text-sm mb-1.5">
                <span className="text-muted-foreground">Missing Rate</span>
                <span className="font-mono font-medium">{dataHealth.missing_rate.toFixed(1)}%</span>
              </div>
              <Progress value={100 - dataHealth.missing_rate * 10} className="h-2" />
            </div>
            <div className="flex justify-between">
              <span className="text-sm text-muted-foreground">Invalid Readings</span>
              <span className={`text-sm font-mono ${dataHealth.invalid_readings > 5 ? "text-warning" : "text-success"}`}>
                {dataHealth.invalid_readings}
              </span>
            </div>
          </div>
        </div>

        {/* Backend Uptime */}
        <div className="glass-card rounded-xl p-5 animate-fade-in">
          <div className="flex items-center gap-2 mb-4">
            <Wifi className="w-5 h-5 text-primary" />
            <h3 className="font-semibold">Backend Status</h3>
          </div>
          <div className="flex flex-col items-center justify-center py-4">
            <div className={`w-16 h-16 rounded-full flex items-center justify-center mb-3 ${
              dataHealth.uptime ? "bg-success/10 kpi-glow-green" : "bg-destructive/10 kpi-glow-red"
            }`}>
              <div className={`w-4 h-4 rounded-full ${dataHealth.uptime ? "bg-success animate-pulse-slow" : "bg-destructive animate-pulse"}`} />
            </div>
            <span className={`text-lg font-bold ${dataHealth.uptime ? "text-success" : "text-destructive"}`}>
              {dataHealth.uptime ? "Online" : "Offline"}
            </span>
            <span className="text-xs text-muted-foreground mt-1">
              Last check: {new Date(dataHealth.last_check).toLocaleTimeString()}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
