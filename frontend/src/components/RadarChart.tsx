"use client";

import React from "react";
import {
  Radar,
  RadarChart as RechartsRadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  ResponsiveContainer,
  Tooltip
} from "recharts";

type Metric = {
  subject: string;
  A: number; // Candidate Score (0-100)
  fullMark: number;
};

type RadarChartProps = {
  metrics: { [key: string]: { normalized: number } };
};

export default function RadarChart({ metrics }: RadarChartProps) {
  if (!metrics || Object.keys(metrics).length === 0) {
    return <div className="text-muted text-sm text-center">No metrics available</div>;
  }

  const data: Metric[] = [
    { subject: "Consistency", A: metrics.consistency?.normalized || 0, fullMark: 100 },
    { subject: "PR Quality", A: metrics.pr_quality?.normalized || 0, fullMark: 100 },
    { subject: "Review Cycles", A: metrics.review_cycles?.normalized || 0, fullMark: 100 },
    { subject: "Collaboration", A: metrics.collaboration?.normalized || 0, fullMark: 100 },
    { subject: "Stability", A: metrics.stability?.normalized || 0, fullMark: 100 },
  ];

  return (
    <div className="w-full h-80 relative flex justify-center">
      <ResponsiveContainer width="100%" height="100%">
        <RechartsRadarChart cx="50%" cy="50%" outerRadius="70%" data={data}>
          <PolarGrid stroke="#e5e5e5" />
          <PolarAngleAxis dataKey="subject" tick={{ fill: "#666", fontSize: 12 }} />
          <PolarRadiusAxis angle={30} domain={[0, 100]} tick={false} axisLine={false} />
          <Radar
            name="Candidate"
            dataKey="A"
            stroke="#ff3e00"
            fill="#ff3e00"
            fillOpacity={0.3}
          />
          <Tooltip 
            contentStyle={{ backgroundColor: "#111", border: "none", borderRadius: "8px", color: "#fff" }}
            itemStyle={{ color: "#fff" }}
          />
        </RechartsRadarChart>
      </ResponsiveContainer>
    </div>
  );
}
