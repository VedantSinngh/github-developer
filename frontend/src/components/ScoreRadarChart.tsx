import React from "react";
import {
  Radar,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  ResponsiveContainer,
} from "recharts";

interface ScoreRadarChartProps {
  metrics: {
    consistency: { normalized: number };
    pr_quality: { normalized: number };
    review_cycles: { normalized: number };
    collaboration: { normalized: number };
    stability: { normalized: number };
  };
}

export const ScoreRadarChart: React.FC<ScoreRadarChartProps> = ({ metrics }) => {
  const data = [
    { subject: "Consistency", score: metrics.consistency.normalized, fullMark: 100 },
    { subject: "PR Quality", score: metrics.pr_quality.normalized, fullMark: 100 },
    { subject: "Review Cycles", score: metrics.review_cycles.normalized, fullMark: 100 },
    { subject: "Collaboration", score: metrics.collaboration.normalized, fullMark: 100 },
    { subject: "Code Stability", score: metrics.stability.normalized, fullMark: 100 },
  ];

  return (
    <div className="bg-surface-card border border-hairline rounded-xl p-6 shadow-soft relative overflow-hidden">
      {/* Background Soft Atmospheric Gradient Orb */}
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-64 h-64 rounded-full gradient-orb-lavender pointer-events-none opacity-40 mix-blend-multiply blur-3xl"></div>
      
      <h3 className="text-caption-uppercase text-muted mb-4 relative z-10">
        Signal Performance Breakdown
      </h3>
      <div className="w-full h-72 relative z-10">
        <ResponsiveContainer width="100%" height="100%">
          <RadarChart cx="50%" cy="50%" outerRadius="75%" data={data}>
            <PolarGrid stroke="#e7e5e4" />
            <PolarAngleAxis
              dataKey="subject"
              stroke="#777169"
              tick={{ fill: "#292524", fontSize: 11, fontFamily: "Inter" }}
            />
            <PolarRadiusAxis angle={30} domain={[0, 100]} stroke="#d6d3d1" />
            <Radar
              name="Candidate Score"
              dataKey="score"
              stroke="#0c0a09"
              fill="#292524"
              fillOpacity={0.15}
            />
          </RadarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};
