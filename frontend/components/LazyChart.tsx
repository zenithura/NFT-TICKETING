import React from 'react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';

interface LazyChartProps {
    data: any[];
}

const LazyChart: React.FC<LazyChartProps> = ({ data }) => {
    return (
        <ResponsiveContainer width="100%" height="100%">
            <BarChart data={data}>
                <XAxis dataKey="name" stroke="#5A5A5A" fontSize={12} tickLine={false} axisLine={false} />
                <YAxis stroke="#5A5A5A" fontSize={12} tickLine={false} axisLine={false} />
                <Tooltip
                    contentStyle={{ backgroundColor: '#202020', border: '1px solid #2F2F2F', borderRadius: '8px', color: '#EFEFEF' }}
                    cursor={{ fill: '#252525' }}
                />
                <Bar dataKey="sales" fill="#F7931A" radius={[4, 4, 0, 0]} />
            </BarChart>
        </ResponsiveContainer>
    );
};

export default LazyChart;
