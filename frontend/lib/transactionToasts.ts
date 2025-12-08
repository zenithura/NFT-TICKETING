/**
 * Transaction Lifecycle Toast System
 * Manages toast notifications for blockchain transactions:
 * pending → confirmed → success/fail
 */

import toast, { Toast } from 'react-hot-toast';
import { ExternalLink, Loader2, CheckCircle2, XCircle } from 'lucide-react';

export interface TransactionToast {
  toastId: string;
  txHash: string;
  message: string;
}

/**
 * Show pending transaction toast
 */
export const showPendingTransaction = (
  txHash: string,
  message: string = 'Transaction pending...'
): string => {
  const toastId = toast.loading(
    (t: Toast) => (
      <div className="flex items-center gap-3">
        <Loader2 className="animate-spin text-primary" size={20} />
        <div className="flex-1">
          <p className="font-medium">{message}</p>
          <p className="text-sm text-foreground-secondary">
            Hash: {txHash.slice(0, 10)}...{txHash.slice(-8)}
          </p>
        </div>
        <a
          href={`https://sepolia.etherscan.io/tx/${txHash}`}
          target="_blank"
          rel="noopener noreferrer"
          className="text-primary hover:text-primary-hover"
          onClick={(e) => e.stopPropagation()}
        >
          <ExternalLink size={16} />
        </a>
      </div>
    ),
    {
      id: txHash,
      duration: Infinity, // Keep until manually dismissed
      position: 'top-right',
    }
  );

  return toastId;
};

/**
 * Update transaction toast to confirmed/success
 */
export const showTransactionSuccess = (
  txHash: string,
  message: string = 'Transaction confirmed!'
): void => {
  toast.success(
    (t: Toast) => (
      <div className="flex items-center gap-3">
        <CheckCircle2 className="text-success" size={20} />
        <div className="flex-1">
          <p className="font-medium">{message}</p>
          <p className="text-sm text-foreground-secondary">
            Hash: {txHash.slice(0, 10)}...{txHash.slice(-8)}
          </p>
        </div>
        <a
          href={`https://sepolia.etherscan.io/tx/${txHash}`}
          target="_blank"
          rel="noopener noreferrer"
          className="text-primary hover:text-primary-hover"
          onClick={(e) => e.stopPropagation()}
        >
          <ExternalLink size={16} />
        </a>
      </div>
    ),
    {
      id: txHash,
      duration: 5000,
      position: 'top-right',
    }
  );
};

/**
 * Update transaction toast to failed
 */
export const showTransactionFailure = (
  txHash: string,
  message: string = 'Transaction failed',
  error?: string
): void => {
  toast.error(
    (t: Toast) => (
      <div className="flex items-center gap-3">
        <XCircle className="text-error" size={20} />
        <div className="flex-1">
          <p className="font-medium">{message}</p>
          {error && (
            <p className="text-sm text-foreground-secondary">{error}</p>
          )}
          <p className="text-sm text-foreground-secondary">
            Hash: {txHash.slice(0, 10)}...{txHash.slice(-8)}
          </p>
        </div>
        <a
          href={`https://sepolia.etherscan.io/tx/${txHash}`}
          target="_blank"
          rel="noopener noreferrer"
          className="text-primary hover:text-primary-hover"
          onClick={(e) => e.stopPropagation()}
        >
          <ExternalLink size={16} />
        </a>
      </div>
    ),
    {
      id: txHash,
      duration: 7000,
      position: 'top-right',
    }
  );
};

/**
 * Monitor transaction and update toast lifecycle
 * This function polls the blockchain to check transaction status
 */
export const monitorTransaction = async (
  txHash: string,
  provider: any,
  onSuccess?: (receipt: any) => void,
  onFailure?: (error: any) => void
): Promise<void> => {
  try {
    // Wait for transaction receipt
    const receipt = await provider.waitForTransaction(txHash, 1, 300000); // 5 min timeout

    if (receipt.status === 1) {
      // Success
      showTransactionSuccess(txHash, 'Transaction confirmed!');
      if (onSuccess) onSuccess(receipt);
    } else {
      // Failed
      showTransactionFailure(txHash, 'Transaction failed', 'Transaction reverted');
      if (onFailure) onFailure(new Error('Transaction reverted'));
    }
  } catch (error: any) {
    // Error waiting for transaction
    showTransactionFailure(
      txHash,
      'Transaction error',
      error.message || 'Failed to confirm transaction'
    );
    if (onFailure) onFailure(error);
  }
};

/**
 * Helper to create a transaction flow with lifecycle toasts
 */
export const executeTransactionWithToasts = async (
  txPromise: Promise<string>, // Returns transaction hash
  provider: any,
  pendingMessage?: string,
  successMessage?: string
): Promise<{ success: boolean; receipt?: any; error?: any }> => {
  try {
    // Execute transaction and get hash
    const txHash = await txPromise;

    // Show pending toast
    showPendingTransaction(txHash, pendingMessage);

    // Monitor transaction
    return new Promise((resolve) => {
      monitorTransaction(
        txHash,
        provider,
        (receipt) => {
          if (successMessage) {
            showTransactionSuccess(txHash, successMessage);
          }
          resolve({ success: true, receipt });
        },
        (error) => {
          resolve({ success: false, error });
        }
      );
    });
  } catch (error: any) {
    // Transaction failed before being sent
    toast.error(error.message || 'Transaction failed to send');
    return { success: false, error };
  }
};

