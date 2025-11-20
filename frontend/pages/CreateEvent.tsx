import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Upload, Loader2, AlertTriangle } from 'lucide-react';
import toast, { Toaster } from 'react-hot-toast';
import { useWeb3 } from '../services/web3Context';
import { UserRole } from '../types';
import { cn } from '../lib/utils';

export const CreateEvent: React.FC = () => {
  const navigate = useNavigate();
  const { userRole, isConnected } = useWeb3();
  const [isSubmitting, setIsSubmitting] = useState(false);
  
  useEffect(() => {
    if (isConnected && userRole !== UserRole.ORGANIZER && userRole !== UserRole.ADMIN) {
      navigate('/dashboard');
    }
  }, [userRole, isConnected, navigate]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    await new Promise(resolve => setTimeout(resolve, 2000));
    toast.success('Event Contract Deployed');
    setTimeout(() => navigate('/dashboard'), 1000);
  };

  if (userRole !== UserRole.ORGANIZER && userRole !== UserRole.ADMIN) return null;

  return (
    <div className="max-w-2xl mx-auto animate-slide-up">
      <Toaster position="bottom-right" />
      
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-foreground mb-2">Create Event</h1>
        <p className="text-foreground-secondary">Deploy a new NFT ticket collection to the blockchain.</p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-8">
        {/* Section 1 */}
        <div className="bg-background-elevated p-6 rounded-xl border border-border space-y-6">
          <h3 className="text-lg font-semibold text-foreground border-b border-border pb-2">Basic Details</h3>
          
          <div className="space-y-4">
            <div>
              <label className="block text-sm text-foreground-secondary mb-1.5">Event Name</label>
              <input required type="text" className="w-full bg-background border border-border rounded-lg px-3 py-2 text-foreground focus:border-primary focus:ring-0 transition-colors" placeholder="e.g. Crypto Summit 2024" />
            </div>
            
            <div>
              <label className="block text-sm text-foreground-secondary mb-1.5">Description</label>
              <textarea required rows={3} className="w-full bg-background border border-border rounded-lg px-3 py-2 text-foreground focus:border-primary focus:ring-0 transition-colors" placeholder="Event details..." />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm text-foreground-secondary mb-1.5">Category</label>
                <select className="w-full bg-background border border-border rounded-lg px-3 py-2 text-foreground focus:border-primary transition-colors">
                  <option>Music</option>
                  <option>Technology</option>
                  <option>Art</option>
                </select>
              </div>
              <div>
                 <label className="block text-sm text-foreground-secondary mb-1.5">Cover Image</label>
                 <div className="border border-dashed border-border rounded-lg px-3 py-2 text-center hover:bg-background-hover cursor-pointer transition-colors">
                   <span className="text-xs text-foreground-secondary flex items-center justify-center gap-2"><Upload size={12} /> Upload</span>
                 </div>
              </div>
            </div>
          </div>
        </div>

        {/* Section 2 */}
        <div className="bg-background-elevated p-6 rounded-xl border border-border space-y-6">
          <h3 className="text-lg font-semibold text-foreground border-b border-border pb-2">Ticket Configuration</h3>
          
          <div className="grid grid-cols-3 gap-4">
            <div>
              <label className="block text-sm text-foreground-secondary mb-1.5">Total Supply</label>
              <input required type="number" className="w-full bg-background border border-border rounded-lg px-3 py-2 text-foreground focus:border-primary" placeholder="1000" />
            </div>
            <div>
              <label className="block text-sm text-foreground-secondary mb-1.5">Price (ETH)</label>
              <input required type="number" step="0.01" className="w-full bg-background border border-border rounded-lg px-3 py-2 text-foreground focus:border-primary" placeholder="0.05" />
            </div>
            <div>
              <label className="block text-sm text-foreground-secondary mb-1.5">Royalty %</label>
              <input required type="number" className="w-full bg-background border border-border rounded-lg px-3 py-2 text-foreground focus:border-primary" placeholder="5" />
            </div>
          </div>

          <div className="bg-primary/5 border border-primary/10 rounded p-3 flex gap-3 items-start">
            <AlertTriangle className="text-primary shrink-0 mt-0.5" size={16} />
            <p className="text-xs text-foreground-secondary">Smart contract deployment is immutable. Ensure all details are correct before confirming.</p>
          </div>
        </div>

        <div className="flex justify-end">
          <button 
            type="submit" 
            disabled={isSubmitting}
            className="bg-primary hover:bg-primary-hover text-white px-8 py-3 rounded-lg font-bold transition-all disabled:opacity-50 flex items-center gap-2"
          >
            {isSubmitting ? <Loader2 className="animate-spin" size={18} /> : 'Deploy Contract'}
          </button>
        </div>
      </form>
    </div>
  );
};
