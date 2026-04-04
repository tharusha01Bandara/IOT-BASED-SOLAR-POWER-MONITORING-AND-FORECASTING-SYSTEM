import { Card } from "@/components/ui/card";
import { MoveRight, MoveLeft } from "lucide-react";

interface ServoGaugeProps {
  angle: number;
  ldrLeft?: number;
  ldrRight?: number;
}

export function ServoGauge({ angle, ldrLeft, ldrRight }: ServoGaugeProps) {
  const normalizedAngle = Math.max(0, Math.min(180, angle));
  const rotation = (normalizedAngle / 180) * 180 - 90;

  return (
    <Card className="col-span-2 md:col-span-4 p-6 bg-card border border-border shadow-sm flex flex-col items-center justify-center relative overflow-hidden group">
      <div className="flex items-center space-x-2 mb-4">
        <h3 className="text-sm font-medium text-muted-foreground mr-1">Tracker Pivot</h3>
        <p className="text-xl font-bold flex items-center">
          {Math.round(normalizedAngle)}�
        </p>
      </div>

      <div className="relative w-48 h-24 mt-2">
        <div className="absolute inset-0 border-t-[16px] border-l-[16px] border-r-[16px] border-muted rounded-t-full border-solid" />
        <div
          className="absolute inset-0 border-t-[16px] border-l-[16px] border-r-[16px] border-primary rounded-t-full transition-all duration-1000 ease-out border-solid"
          style={{
            clipPath: "polygon(0 0, 100% 0, 100% 100%, 0 100%)",
            transformOrigin: "bottom center",
            transform: `rotate(${rotation}deg)`,
          }}
        />
        <div className="absolute bottom-0 left-[50%] -translate-x-1/2 translate-y-1/2 w-4 h-4 bg-background border-4 border-primary rounded-full z-10" />
      </div>

      <div className="flex w-full justify-between items-center mt-6 px-12 text-xs text-muted-foreground">
        <div className="flex flex-col items-center">
            <MoveLeft className="w-4 h-4 mb-1" />
            <span>East (0�)</span>
            {ldrLeft !== undefined && <span className="text-[10px] mt-1 opacity-70">LDR: {ldrLeft}</span>}
        </div>
        <div className="flex flex-col items-center">
            <MoveRight className="w-4 h-4 mb-1" />
            <span>West (180�)</span>
            {ldrRight !== undefined && <span className="text-[10px] mt-1 opacity-70">LDR: {ldrRight}</span>}
        </div>
      </div>
    </Card>
  );
}
