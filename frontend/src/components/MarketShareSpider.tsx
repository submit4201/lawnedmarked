import {
    Radar, RadarChart, PolarGrid,
    PolarAngleAxis, ResponsiveContainer, PolarRadiusAxis
} from 'recharts';

interface SpiderData {
    axis: string;
    value: number;
    fullMark?: number;
}

interface MarketShareSpiderProps {
    data: SpiderData[];
    label?: string;
}

export const MarketShareSpider = ({ data }: MarketShareSpiderProps) => {
    // Add fullMark for proper scaling
    const chartData = data.map(d => ({ ...d, fullMark: 100 }));

    return (
        <div className="h-[200px] w-full">
            <ResponsiveContainer width="100%" height="100%">
                <RadarChart cx="50%" cy="50%" outerRadius="70%" data={chartData}>
                    <PolarGrid
                        stroke="rgba(255,255,255,0.1)"
                        strokeDasharray="3 3"
                    />
                    <PolarAngleAxis
                        dataKey="axis"
                        tick={{
                            fill: '#6b7280',
                            fontSize: 9,
                            fontFamily: 'JetBrains Mono, monospace',
                            textAnchor: 'middle'
                        }}
                        tickLine={false}
                    />
                    <PolarRadiusAxis
                        angle={90}
                        domain={[0, 100]}
                        tick={false}
                        axisLine={false}
                    />
                    <Radar
                        name="Performance"
                        dataKey="value"
                        stroke="#00f5ff"
                        fill="url(#radarGradient)"
                        fillOpacity={0.5}
                        strokeWidth={2}
                        dot={{
                            r: 3,
                            fill: '#00f5ff',
                            strokeWidth: 0
                        }}
                    />
                    <defs>
                        <linearGradient id="radarGradient" x1="0" y1="0" x2="1" y2="1">
                            <stop offset="0%" stopColor="#00f5ff" stopOpacity={0.4} />
                            <stop offset="100%" stopColor="#bf00ff" stopOpacity={0.4} />
                        </linearGradient>
                    </defs>
                </RadarChart>
            </ResponsiveContainer>
        </div>
    );
};
