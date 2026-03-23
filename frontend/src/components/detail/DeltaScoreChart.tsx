import {
  BarChart, Bar, XAxis, YAxis, Tooltip,
  ReferenceLine, ResponsiveContainer, Cell,
} from "recharts";

interface Props {
  scores: Record<string, number>;
  outputType: string;
}

export function DeltaScoreChart({ scores, outputType }: Props) {
  const data = Object.entries(scores)
    .map(([tissue, value]) => ({ tissue, value }))
    .sort((a, b) => Math.abs(b.value) - Math.abs(a.value))
    .slice(0, 8);

  if (data.length === 0) return (
    <p className="text-xs text-[#3c4f3d]/40 py-4 text-center">No data</p>
  );

  return (
    <div>
      <p className="text-xs font-medium text-[#3c4f3d]/60 mb-2">{outputType}</p>
      <ResponsiveContainer width="100%" height={180}>
        <BarChart data={data} layout="vertical" margin={{ left: 8, right: 16 }}>
          <XAxis
            type="number"
            domain={[-1, 1]}
            tick={{ fontSize: 10, fill: "rgba(60,79,61,0.5)" }}
            tickLine={false}
            axisLine={false}
          />
          <YAxis
            type="category"
            dataKey="tissue"
            width={90}
            tick={{ fontSize: 10, fill: "rgba(60,79,61,0.7)" }}
            tickLine={false}
            axisLine={false}
          />
          <Tooltip
            contentStyle={{
              background: "#fff",
              border: "1px solid rgba(60,79,61,0.1)",
              borderRadius: 6,
              fontSize: 11,
            }}
            formatter={(v: number) => [v.toFixed(4), "δ score"]}
          />
          <ReferenceLine x={0} stroke="rgba(60,79,61,0.2)" />
          <Bar dataKey="value" radius={[0, 3, 3, 0]}>
            {data.map((entry) => (
              <Cell
                key={entry.tissue}
                fill={entry.value < 0 ? "#de8246" : "#3c4f3d"}
                fillOpacity={0.75}
              />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}