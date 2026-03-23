import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

interface Props {
  data: {
    gene: string;
    delta_score: number;
    splicing_score: number;
  }[];
}

export default function DeltaScoreChart({ data }: Props) {
  const validData = data.filter(d => d.delta_score != null);

  if (validData.length === 0) return <p className="text-gray-500 italic p-4 text-center">No structural/splicing score data available</p>;

  return (
    <div className="h-64 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={validData}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="gene" />
          <YAxis />
          <Tooltip />
          <Legend />
          <Bar dataKey="delta_score" fill="#3b82f6" name="Delta Score" />
          <Bar dataKey="splicing_score" fill="#10b981" name="Splicing Score" />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
