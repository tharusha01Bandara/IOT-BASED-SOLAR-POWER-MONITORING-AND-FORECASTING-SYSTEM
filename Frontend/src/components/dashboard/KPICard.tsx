import { ReactNode } from "react";
import { Area, AreaChart, ResponsiveContainer } from "recharts";
import { StatusColor } from "@/types/solar";

interface KPICardProps {
  title: string;
  value: string | number;
  unit: string;
  icon: ReactNode;
  status: StatusColor;
  sparklineData?: number[];
  sparklineColor?: string;
  subtitle?: string;
}

const statusStyles: Record<StatusColor, string> = {
  normal: "kpi-glow-green border-success/20",
  warning: "kpi-glow-amber border-warning/20",
  critical: "kpi-glow-red border-destructive/20",
  offline: "border-border opacity-60",
};

const statusDotColor: Record<StatusColor, string> = {
  normal: "bg-success",
  warning: "bg-warning",
  critical: "bg-destructive",
  offline: "bg-offline",
};

const defaultSparkColors: Record<StatusColor, string> = {
  normal: "hsl(152, 60%, 45%)",
  warning: "hsl(38, 92%, 50%)",
  critical: "hsl(0, 72%, 55%)",
  offline: "hsl(220, 10%, 50%)",
};

export function KPICard({ title, value, unit, icon, status, sparklineData, sparklineColor, subtitle }: KPICardProps) {
  const chartData = sparklineData?.map((v, i) => ({ v, i })) || [];
  const color = sparklineColor || defaultSparkColors[status];

  return (
    <div className={`glass-card rounded-xl p-4 animate-fade-in ${statusStyles[status]} transition-all hover:scale-[1.02]`}>
      <div className="flex items-start justify-between mb-2">
        <div className="flex items-center gap-2">
          <div className="text-muted-foreground">{icon}</div>
          <span className="text-xs font-medium text-muted-foreground uppercase tracking-wider">{title}</span>
        </div>
        <div className={`w-2 h-2 rounded-full ${statusDotColor[status]} ${status === "normal" ? "animate-pulse-slow" : status === "critical" ? "animate-pulse" : ""}`} />
      </div>

      <div className="flex items-end justify-between">
        <div>
          <div className="text-2xl md:text-3xl font-bold font-mono tracking-tight">{value}</div>
          <div className="text-[11px] text-muted-foreground mt-0.5">
            {unit} {subtitle && <span className="ml-1">· {subtitle}</span>}
          </div>
        </div>

        {chartData.length > 2 && (
          <div className="w-20 h-10 opacity-70">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={chartData}>
                <defs>
                  <linearGradient id={`grad-${title}`} x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor={color} stopOpacity={0.4} />
                    <stop offset="100%" stopColor={color} stopOpacity={0} />
                  </linearGradient>
                </defs>
                <Area type="monotone" dataKey="v" stroke={color} strokeWidth={1.5} fill={`url(#grad-${title})`} dot={false} />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        )}
      </div>
    </div>
  );
}
