import React from 'react';
import { useWeb3 } from '../services/web3Context';
import { UserRole } from '../types';
import { Shield, Users, Activity, Settings, Search } from 'lucide-react';

export const AdminDashboard: React.FC = () => {
  const { isConnected, userRole } = useWeb3();

  if (!isConnected || userRole !== UserRole.ADMIN) {
    return <div className="text-center py-20 text-foreground-secondary">Restricted Access</div>;
  }

  return (
    <div className="space-y-8 animate-fade-in">
      <div className="flex justify-between items-end border-b border-border pb-6">
        <div>
          <h1 className="text-3xl font-bold text-foreground flex items-center gap-3">
            <Shield className="text-error" size={28} />
            Platform Admin
          </h1>
          <p className="text-foreground-secondary mt-1">System overview and user management.</p>
        </div>
        <div className="text-xs font-mono text-error bg-error/10 px-3 py-1 rounded border border-error/20">
          SUPER_ADMIN_MODE
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        {['Total Users', 'Active Events', 'Revenue (ETH)', 'Disputes'].map((label, i) => (
          <div key={label} className="bg-background-elevated p-4 rounded-lg border border-border">
            <p className="text-xs text-foreground-tertiary uppercase font-bold">{label}</p>
            <p className="text-2xl font-bold text-foreground mt-1">{['12,450', '85', '145.2', '12'][i]}</p>
          </div>
        ))}
      </div>

      <div className="bg-background-elevated rounded-xl border border-border overflow-hidden">
        <div className="p-4 border-b border-border flex justify-between items-center bg-background-hover/50">
          <h3 className="font-bold text-foreground flex items-center gap-2"><Users size={16} /> Users</h3>
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-foreground-tertiary" size={14} />
            <input type="text" placeholder="Search..." className="bg-background border border-border rounded pl-9 pr-3 py-1 text-sm focus:border-primary w-48" />
          </div>
        </div>
        <table className="w-full text-left text-sm">
          <thead className="bg-background text-foreground-secondary border-b border-border">
            <tr>
              <th className="px-6 py-3 font-medium">Address</th>
              <th className="px-6 py-3 font-medium">Role</th>
              <th className="px-6 py-3 font-medium">Status</th>
              <th className="px-6 py-3 font-medium text-right">Action</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border">
            {[1,2,3].map((i) => (
              <tr key={i} className="hover:bg-background-hover transition-colors">
                <td className="px-6 py-4 font-mono text-foreground-secondary">0x71C...9A2{i}</td>
                <td className="px-6 py-4">
                  <span className="px-2 py-1 rounded text-xs border bg-primary/10 border-primary/20 text-primary">
                    {['Organizer', 'Buyer', 'Reseller'][i-1]}
                  </span>
                </td>
                <td className="px-6 py-4 text-success">Active</td>
                <td className="px-6 py-4 text-right">
                  <button className="text-foreground-tertiary hover:text-error transition-colors text-xs font-medium">Ban User</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};
