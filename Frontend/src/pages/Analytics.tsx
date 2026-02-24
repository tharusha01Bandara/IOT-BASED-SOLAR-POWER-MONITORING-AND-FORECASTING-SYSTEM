import { useMemo } from "react";
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend,
  ScatterChart, Scatter, AreaChart, Area,
} from "recharts";
import { useSolarContext } from "@/contexts/SolarDataContext";

function formatTime(ts: string) {
  return new Date(ts).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

export default function Analytics() {
  const { historicalData, timeRange } = useSolarContext();

  const chartData = useMemo(() =>
    historicalData.map((d) => ({
      time: formatTime(d.timestamp),
      power: d.power,
      lux: d.lux,
      temperature: d.temperature,
      predicted: Math.max(0, d.power + (Math.random() - 0.5) * 30),
    })),
    [historicalData]
  );

  const scatterData = useMemo(() =>
    historicalData.map((d) => ({ lux: d.lux, power: d.power })),
    [historicalData]
  );

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      <div>
        <h1 className="text-xl md:text-2xl font-bold">Analytics</h1>
        <p className="text-sm text-muted-foreground mt-0.5">Historical trends and correlations ({timeRange})</p>
      </div>

      {/* Power over Time */}
      <div className="glass-card rounded-xl p-4 animate-fade-in">
        <h3 className="text-sm font-semibold mb-4">Power Output vs Time</h3>
        <div className="h-64 md:h-80">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={chartData}>
              <defs>
                <linearGradient id="powerGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="hsl(174, 72%, 45%)" stopOpacity={0.3} />
                  <stop offset="100%" stopColor="hsl(174, 72%, 45%)" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" className="opacity-20" />
              <XAxis dataKey="time" tick={{ fontSize: 10 }} className="text-muted-foreground" />
              <YAxis tick={{ fontSize: 10 }} className="text-muted-foreground" />
              <Tooltip contentStyle={{ background: "hsl(222, 25%, 12%)", border: "1px solid hsl(222, 20%, 18%)", borderRadius: "8px", fontSize: 12 }} />
              <Area type="monotone" dataKey="power" stroke="hsl(174, 72%, 45%)" strokeWidth={2} fill="url(#powerGrad)" name="Power (W)" />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Predicted vs Actual */}
      <div className="glass-card rounded-xl p-4 animate-fade-in">
        <h3 className="text-sm font-semibold mb-4">Predicted vs Actual Power</h3>
        <div className="h-64 md:h-80">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" className="opacity-20" />
              <XAxis dataKey="time" tick={{ fontSize: 10 }} />
              <YAxis tick={{ fontSize: 10 }} />
              <Tooltip contentStyle={{ background: "hsl(222, 25%, 12%)", border: "1px solid hsl(222, 20%, 18%)", borderRadius: "8px", fontSize: 12 }} />
              <Legend />
              <Line type="monotone" dataKey="power" stroke="hsl(174, 72%, 45%)" strokeWidth={2} dot={false} name="Actual (W)" />
              <Line type="monotone" dataKey="predicted" stroke="hsl(265, 60%, 60%)" strokeWidth={2} dot={false} strokeDasharray="5 5" name="Predicted (W)" />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="grid md:grid-cols-2 gap-4">
        {/* Lux Chart */}
        <div className="glass-card rounded-xl p-4 animate-fade-in">
          <h3 className="text-sm font-semibold mb-4">Lux vs Time</h3>
          <div className="h-52">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={chartData}>
                <defs>
                  <linearGradient id="luxGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="hsl(45, 95%, 55%)" stopOpacity={0.3} />
                    <stop offset="100%" stopColor="hsl(45, 95%, 55%)" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" className="opacity-20" />
                <XAxis dataKey="time" tick={{ fontSize: 9 }} />
                <YAxis tick={{ fontSize: 9 }} />
                <Tooltip contentStyle={{ background: "hsl(222, 25%, 12%)", border: "1px solid hsl(222, 20%, 18%)", borderRadius: "8px", fontSize: 12 }} />
                <Area type="monotone" dataKey="lux" stroke="hsl(45, 95%, 55%)" strokeWidth={2} fill="url(#luxGrad)" name="Lux" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Scatter: Lux vs Power */}
        <div className="glass-card rounded-xl p-4 animate-fade-in">
          <h3 className="text-sm font-semibold mb-4">Lux vs Power (Correlation)</h3>
          <div className="h-52">
            <ResponsiveContainer width="100%" height="100%">
              <ScatterChart>
                <CartesianGrid strokeDasharray="3 3" className="opacity-20" />
                <XAxis dataKey="lux" tick={{ fontSize: 9 }} name="Lux" />
                <YAxis dataKey="power" tick={{ fontSize: 9 }} name="Power" />
                <Tooltip contentStyle={{ background: "hsl(222, 25%, 12%)", border: "1px solid hsl(222, 20%, 18%)", borderRadius: "8px", fontSize: 12 }} />
                <Scatter data={scatterData} fill="hsl(174, 72%, 45%)" fillOpacity={0.6} />
              </ScatterChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
    </div>
  );
}
