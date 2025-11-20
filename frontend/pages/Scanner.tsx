
import React, { useState, useEffect } from 'react';
import { Camera, CheckCircle, XCircle, RefreshCw, AlertTriangle, ArrowLeft } from 'lucide-react';
import { Link, useNavigate } from 'react-router-dom';
import { useWeb3 } from '../services/web3Context';
import { UserRole } from '../types';

export const Scanner: React.FC = () => {
  const { userRole, isConnected } = useWeb3();
  const navigate = useNavigate();
  const [scanning, setScanning] = useState(true);
  const [result, setResult] = useState<'idle' | 'valid' | 'invalid' | 'used'>('idle');
  const [scannedData, setScannedData] = useState<string>('');

  useEffect(() => {
    // In a real app, we would check if userRole is SCANNER or ADMIN
    // For demo purposes, if not connected, just show unauthorized
  }, [userRole]);

  if (!isConnected || (userRole !== UserRole.SCANNER && userRole !== UserRole.ADMIN && userRole !== UserRole.ORGANIZER)) {
     return (
         <div className="min-h-screen bg-black flex flex-col items-center justify-center p-6 text-center">
             <AlertTriangle className="text-red-500 w-16 h-16 mb-4" />
             <h2 className="text-2xl font-bold text-white mb-2">Unauthorized Access</h2>
             <p className="text-gray-400 mb-8">You need the 'Scanner' role to access this tool.</p>
             <Link to="/" className="text-orange-400 hover:underline">Return Home</Link>
         </div>
     )
  }

  const simulateScan = () => {
    setScanning(false);
    // Randomly simulate result
    const random = Math.random();
    const mockAddress = '0x71...9A23';
    
    if (random > 0.6) {
      setResult('valid');
      setScannedData(`Ticket #1042 - Valid - Owner: ${mockAddress}`);
    } else if (random > 0.3) {
      setResult('used');
      setScannedData(`Ticket #309 - Already Used - Entry: 19:00`);
    } else {
      setResult('invalid');
      setScannedData('Invalid Signature / Fake Ticket');
    }
  };

  const reset = () => {
    setScanning(true);
    setResult('idle');
    setScannedData('');
  };

  return (
    <div className="min-h-screen bg-black flex flex-col items-center justify-center p-4 relative">
      <Link to="/dashboard" className="absolute top-4 left-4 text-gray-400 hover:text-white flex items-center gap-2 z-20">
        <ArrowLeft size={20} /> Exit
      </Link>

      <div className="w-full max-w-md bg-gray-900 rounded-3xl overflow-hidden border-4 border-gray-800 shadow-2xl relative">
        
        <div className="p-6 bg-gray-800 flex justify-between items-center z-10 relative">
          <div>
             <h2 className="text-white font-bold text-xl">Gate Scanner</h2>
             <p className="text-xs text-green-400 flex items-center gap-1"><span className="w-2 h-2 bg-green-500 rounded-full animate-pulse"/> Online • {userRole}</p>
          </div>
          <div className="p-2 bg-gray-700 rounded-lg">
             <Camera size={20} className="text-gray-300" />
          </div>
        </div>

        <div className="relative aspect-[3/4] bg-black flex items-center justify-center overflow-hidden">
          {scanning ? (
            <>
              {/* Camera Simulation */}
              <img 
                src="https://images.unsplash.com/photo-1492684223066-81342ee5ff30?auto=format&fit=crop&w=800&q=80" 
                className="absolute inset-0 w-full h-full object-cover opacity-50" 
                alt="Camera Feed"
              />
              <div className="absolute inset-0 bg-gradient-to-b from-black/50 via-transparent to-black/50" />
              
              <div className="absolute inset-0 flex items-center justify-center">
                <div className="w-64 h-64 border-2 border-orange-500/50 rounded-2xl relative">
                   <div className="absolute top-0 left-0 w-8 h-8 border-t-4 border-l-4 border-orange-500 -mt-1 -ml-1 rounded-tl-lg"></div>
                   <div className="absolute top-0 right-0 w-8 h-8 border-t-4 border-r-4 border-orange-500 -mt-1 -mr-1 rounded-tr-lg"></div>
                   <div className="absolute bottom-0 left-0 w-8 h-8 border-b-4 border-l-4 border-orange-500 -mb-1 -ml-1 rounded-bl-lg"></div>
                   <div className="absolute bottom-0 right-0 w-8 h-8 border-b-4 border-r-4 border-orange-500 -mb-1 -mr-1 rounded-br-lg"></div>
                   <div className="w-full h-0.5 bg-red-500/80 absolute top-1/2 transform -translate-y-1/2 shadow-[0_0_15px_rgba(239,68,68,0.8)]"></div>
                </div>
              </div>
              
              <div className="absolute bottom-10 w-full px-10">
                <button 
                    onClick={simulateScan}
                    className="w-full bg-orange-600 text-white py-4 rounded-2xl font-bold shadow-lg shadow-orange-900/50 hover:bg-orange-500 transition-all active:scale-95"
                >
                    Tap to Scan Code
                </button>
              </div>
            </>
          ) : (
            <div className="flex flex-col items-center justify-center p-8 text-center space-y-6 z-10 w-full h-full bg-gray-900/90 backdrop-blur-md">
              {result === 'valid' && (
                <div className="animate-in zoom-in duration-300 flex flex-col items-center">
                  <div className="w-28 h-28 rounded-full bg-green-500/20 flex items-center justify-center mb-6 border-4 border-green-500/50">
                    <CheckCircle className="w-16 h-16 text-green-500" />
                  </div>
                  <h3 className="text-3xl font-bold text-white mb-2">ACCESS GRANTED</h3>
                  <div className="bg-gray-800 p-4 rounded-xl border border-gray-700 w-full mb-4 shadow-inner">
                    <p className="text-green-400 font-mono text-sm font-medium">{scannedData}</p>
                  </div>
                </div>
              )}
              {result === 'used' && (
                <div className="animate-in zoom-in duration-300 flex flex-col items-center">
                   <div className="w-28 h-28 rounded-full bg-yellow-500/20 flex items-center justify-center mb-6 border-4 border-yellow-500/50">
                    <AlertTriangle className="w-16 h-16 text-yellow-500" />
                  </div>
                  <h3 className="text-3xl font-bold text-white mb-2">ALREADY SCANNED</h3>
                  <div className="bg-gray-800 p-4 rounded-xl border border-gray-700 w-full mb-4 shadow-inner">
                    <p className="text-yellow-400 font-mono text-sm font-medium">{scannedData}</p>
                  </div>
                </div>
              )}
              {result === 'invalid' && (
                 <div className="animate-in zoom-in duration-300 flex flex-col items-center">
                   <div className="w-28 h-28 rounded-full bg-red-500/20 flex items-center justify-center mb-6 border-4 border-red-500/50">
                    <XCircle className="w-16 h-16 text-red-500" />
                  </div>
                  <h3 className="text-3xl font-bold text-white mb-2">ACCESS DENIED</h3>
                  <div className="bg-gray-800 p-4 rounded-xl border border-gray-700 w-full mb-4 shadow-inner">
                    <p className="text-red-400 font-mono text-sm font-medium">{scannedData}</p>
                  </div>
                </div>
              )}

              <button onClick={reset} className="mt-4 flex items-center justify-center w-full py-4 rounded-xl bg-gray-800 hover:bg-gray-700 text-white font-medium transition-colors border border-gray-700">
                <RefreshCw className="mr-2" size={20} /> Scan Next Ticket
              </button>
            </div>
          )}
        </div>
      </div>
      
      <p className="mt-6 text-gray-500 text-xs max-w-xs text-center font-mono">
        Secured by Ticket721 Protocol. Verification happens on-chain.
      </p>
    </div>
  );
};
