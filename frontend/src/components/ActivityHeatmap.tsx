import React from "react";

interface ActivityHeatmapProps {
  startDate: string;
  endDate: string;
  activities?: { date: string; count: number }[];
}

export const ActivityHeatmap: React.FC<ActivityHeatmapProps> = ({
  startDate,
  endDate,
  activities = [],
}) => {
  const days = Array.from({ length: 14 }, (_, i) => {
    const d = new Date();
    d.setDate(d.getDate() - (13 - i));
    const dateStr = d.toISOString().split("T")[0];
    const match = activities.find((a) => a.date === dateStr);
    return {
      date: dateStr,
      count: match ? match.count : 0,
    };
  });

  const getColorClass = (count: number) => {
    if (count === 0) return "bg-surface-strong border border-hairline-soft";
    if (count < 3) return "bg-hairline-strong text-ink";
    if (count < 5) return "bg-ink-primary text-on-primary";
    return "bg-ink text-on-primary font-bold";
  };

  return (
    <div className="bg-surface-card border border-hairline rounded-xl p-6 shadow-soft space-y-4">
      <div className="flex justify-between items-center">
        <h4 className="text-caption-uppercase text-muted">
          Window Activity Streak Heatmap
        </h4>
        <span className="text-caption text-muted font-sans">
          {startDate} — {endDate}
        </span>
      </div>
      <div className="flex gap-2 justify-between items-center overflow-x-auto py-2">
        {days.map((day) => (
          <div key={day.date} className="flex flex-col items-center gap-1.5 group">
            <div
              className={`w-9 h-9 rounded-lg ${getColorClass(
                day.count
              )} transition-transform group-hover:scale-105 flex items-center justify-center text-caption font-sans`}
              title={`${day.date}: ${day.count} activities`}
            >
              {day.count > 0 ? day.count : ""}
            </div>
            <span className="text-[10px] text-muted-soft">{day.date.slice(5)}</span>
          </div>
        ))}
      </div>
    </div>
  );
};
