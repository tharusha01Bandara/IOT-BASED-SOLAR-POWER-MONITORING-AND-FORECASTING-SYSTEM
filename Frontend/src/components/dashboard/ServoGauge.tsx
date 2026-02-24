import { useEffect, useRef, useState } from "react";

interface ServoGaugeProps {
  angle: number; // 0–180
}

const ZONES = [
  { min: 0, max: 30, label: "Edge", color: "hsl(38, 92%, 50%)", bg: "hsl(38, 92%, 50%)" },
  { min: 30, max: 60, label: "Tracking", color: "hsl(152, 60%, 45%)", bg: "hsl(152, 60%, 45%)" },
  { min: 60, max: 120, label: "Optimal", color: "hsl(170, 70%, 45%)", bg: "hsl(170, 70%, 45%)" },
  { min: 120, max: 150, label: "Tracking", color: "hsl(152, 60%, 45%)", bg: "hsl(152, 60%, 45%)" },
  { min: 150, max: 180, label: "Edge", color: "hsl(38, 92%, 50%)", bg: "hsl(38, 92%, 50%)" },
];

function getZone(angle: number) {
  return ZONES.find((z) => angle >= z.min && angle <= z.max) || ZONES[2];
}

function polarToCartesian(cx: number, cy: number, r: number, angleDeg: number) {
  const rad = ((angleDeg - 180) * Math.PI) / 180;
  return { x: cx + r * Math.cos(rad), y: cy + r * Math.sin(rad) };
}

function describeArc(cx: number, cy: number, r: number, startAngle: number, endAngle: number) {
  const start = polarToCartesian(cx, cy, r, endAngle);
  const end = polarToCartesian(cx, cy, r, startAngle);
  const largeArc = endAngle - startAngle > 180 ? 1 : 0;
  return `M ${end.x} ${end.y} A ${r} ${r} 0 ${largeArc} 1 ${start.x} ${start.y}`;
}

export function ServoGauge({ angle }: ServoGaugeProps) {
  const [displayAngle, setDisplayAngle] = useState(angle);
  const [pulse, setPulse] = useState(false);
  const prevAngle = useRef(angle);
  const animRef = useRef<number>(0);

  // Smooth animated needle
  useEffect(() => {
    if (prevAngle.current === angle) return;
    const from = prevAngle.current;
    const to = angle;
    const duration = 600;
    const start = performance.now();
    prevAngle.current = angle;

    setPulse(true);
    const timeout = setTimeout(() => setPulse(false), 400);

    const animate = (now: number) => {
      const t = Math.min((now - start) / duration, 1);
      const ease = 1 - Math.pow(1 - t, 3); // easeOutCubic
      setDisplayAngle(from + (to - from) * ease);
      if (t < 1) animRef.current = requestAnimationFrame(animate);
    };
    animRef.current = requestAnimationFrame(animate);

    return () => {
      cancelAnimationFrame(animRef.current);
      clearTimeout(timeout);
    };
  }, [angle]);

  const zone = getZone(displayAngle);
  const cx = 120, cy = 110, r = 85;
  const needleAngle = displayAngle; // 0=left, 180=right
  const needleEnd = polarToCartesian(cx, cy, r - 12, needleAngle);
  const needleBase1 = polarToCartesian(cx, cy, 6, needleAngle - 90);
  const needleBase2 = polarToCartesian(cx, cy, 6, needleAngle + 90);

  return (
    <div className={`glass-card rounded-xl p-4 animate-fade-in transition-all hover:scale-[1.02] border-border/30 ${pulse ? "ring-1 ring-primary/20" : ""}`}>
      <div className="flex items-center gap-2 mb-1">
        <span className="text-xs font-medium text-muted-foreground uppercase tracking-wider">Servo Angle</span>
        <div className={`ml-auto px-2 py-0.5 rounded-full text-[10px] font-semibold transition-colors duration-500`}
          style={{ backgroundColor: zone.bg + "22", color: zone.color }}>
          {zone.label}
        </div>
      </div>

      <svg viewBox="0 0 240 135" className="w-full max-w-[260px] mx-auto">
        <defs>
          {/* Glow filter */}
          <filter id="servo-glow" x="-50%" y="-50%" width="200%" height="200%">
            <feGaussianBlur in="SourceGraphic" stdDeviation="6" result="blur" />
            <feMerge>
              <feMergeNode in="blur" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
          {/* Inner shadow */}
          <filter id="servo-inner-shadow">
            <feGaussianBlur in="SourceAlpha" stdDeviation="3" result="blur" />
            <feOffset dx="0" dy="2" result="offset" />
            <feComposite in="offset" in2="SourceAlpha" operator="arithmetic" k2="-1" k3="1" result="shadow" />
            <feFlood floodColor="black" floodOpacity="0.25" result="color" />
            <feComposite in="color" in2="shadow" operator="in" result="finalShadow" />
            <feMerge>
              <feMergeNode in="SourceGraphic" />
              <feMergeNode in="finalShadow" />
            </feMerge>
          </filter>
          {/* Active arc gradient */}
          <linearGradient id="servo-arc-grad" x1="0" y1="0" x2="1" y2="0">
            <stop offset="0%" stopColor="hsl(38, 92%, 50%)" stopOpacity="0.7" />
            <stop offset="30%" stopColor="hsl(152, 60%, 45%)" stopOpacity="0.9" />
            <stop offset="50%" stopColor="hsl(170, 70%, 45%)" stopOpacity="1" />
            <stop offset="70%" stopColor="hsl(152, 60%, 45%)" stopOpacity="0.9" />
            <stop offset="100%" stopColor="hsl(38, 92%, 50%)" stopOpacity="0.7" />
          </linearGradient>
        </defs>

        {/* Background track with inner shadow */}
        <path
          d={describeArc(cx, cy, r, 0, 180)}
          fill="none"
          stroke="hsl(var(--muted))"
          strokeWidth="14"
          strokeLinecap="round"
          filter="url(#servo-inner-shadow)"
          opacity="0.5"
        />

        {/* Active arc with glow */}
        <path
          d={describeArc(cx, cy, r, 0, Math.max(1, displayAngle))}
          fill="none"
          stroke="url(#servo-arc-grad)"
          strokeWidth="10"
          strokeLinecap="round"
          filter="url(#servo-glow)"
          className="transition-all duration-300"
        />

        {/* Tick marks */}
        {[0, 30, 60, 90, 120, 150, 180].map((tick) => {
          const outer = polarToCartesian(cx, cy, r + 10, tick);
          const inner = polarToCartesian(cx, cy, r + 4, tick);
          return (
            <line key={tick} x1={inner.x} y1={inner.y} x2={outer.x} y2={outer.y}
              stroke="hsl(var(--muted-foreground))" strokeWidth="1.5" opacity="0.4" strokeLinecap="round" />
          );
        })}

        {/* Tick labels */}
        {[0, 90, 180].map((tick) => {
          const pos = polarToCartesian(cx, cy, r + 20, tick);
          return (
            <text key={`l-${tick}`} x={pos.x} y={pos.y + 4} textAnchor="middle"
              className="fill-muted-foreground" fontSize="10" fontWeight="500">
              {tick}°
            </text>
          );
        })}

        {/* Needle */}
        <polygon
          points={`${needleEnd.x},${needleEnd.y} ${needleBase1.x},${needleBase1.y} ${needleBase2.x},${needleBase2.y}`}
          style={{ fill: zone.color, transition: "fill 0.5s" }}
          filter="url(#servo-glow)"
        />

        {/* Center hub */}
        <circle cx={cx} cy={cy} r="8" fill="hsl(var(--card))" stroke="hsl(var(--border))" strokeWidth="2" />
        <circle cx={cx} cy={cy} r="3" style={{ fill: zone.color, transition: "fill 0.5s" }} />

        {/* Value text */}
        <text x={cx} y={cy + 30} textAnchor="middle" fontSize="22" fontWeight="bold"
          fontFamily="monospace" style={{ fill: zone.color, transition: "fill 0.5s" }}
          className={pulse ? "animate-pulse" : ""}>
          {Math.round(displayAngle)}°
        </text>
      </svg>
    </div>
  );
}
