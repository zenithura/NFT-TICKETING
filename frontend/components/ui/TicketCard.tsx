import React from 'react';
import { Link } from 'react-router-dom';
import { Calendar, MapPin } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { Event } from '../../types';
import { OptimizedImage } from './OptimizedImage';
import { cn } from '../../lib/utils';

interface TicketCardProps {
    event: Event;
    index: number;
}

/**
 * Optimized TicketCard component.
 * Features:
 * - React.memo for performance
 * - Uses OptimizedImage for LCP/CLS
 * - Explicit dimensions to match skeleton
 */
export const TicketCard: React.FC<TicketCardProps> = React.memo(({ event, index }) => {
    const { t, i18n } = useTranslation();

    return (
        <Link
            to={`/event/${event.id}`}
            className="group bg-background-elevated rounded-xl border border-border overflow-hidden card-hover flex flex-col h-full"
            style={{ contentVisibility: index > 5 ? 'auto' : 'visible' }}
        >
            <OptimizedImage
                src={event.imageUrl}
                alt={event.title}
                width={640}
                height={360}
                loading={index < 2 ? "eager" : "lazy"}
                fetchPriority={index === 0 ? "high" : "auto"}
                containerClassName="w-full"
                className="group-hover:scale-105"
            />

            <div className="p-5 space-y-4 flex-grow flex flex-col">
                <div>
                    <div className="flex items-center justify-between mb-1">
                        <span className="text-xs font-medium text-primary uppercase tracking-wider">{event.category}</span>
                        <span className="text-xs text-foreground-tertiary">
                            {event.totalTickets - event.soldTickets} {t('marketplace.ticketsLeft', 'left')}
                        </span>
                    </div>
                    <h3 className="text-lg font-bold text-foreground group-hover:text-primary transition-colors line-clamp-1">
                        {event.title}
                    </h3>
                </div>

                <div className="space-y-2 flex-grow">
                    <div className="flex items-center gap-2 text-sm text-foreground-secondary">
                        <Calendar size={14} />
                        <span>
                            {new Date(event.date).toLocaleDateString(i18n.language === 'az' ? 'az-AZ' : 'en-US', {
                                year: 'numeric',
                                month: 'long',
                                day: 'numeric'
                            })}
                        </span>
                    </div>
                    <div className="flex items-center gap-2 text-sm text-foreground-secondary">
                        <MapPin size={14} />
                        <span className="line-clamp-1">{event.location}</span>
                    </div>
                </div>

                <div className="pt-4 border-t border-border flex items-center justify-between mt-auto">
                    <div className="flex items-center gap-2">
                        <div className="w-5 h-5 rounded-full bg-gradient-to-br from-orange-500 to-yellow-500" />
                        <span className="text-xs text-foreground-secondary">
                            {t('marketplace.by', 'by')} {event.organizer.slice(0, 6)}...
                        </span>
                    </div>
                    <div className="text-sm font-mono font-bold text-foreground">
                        {event.price} {event.currency}
                    </div>
                </div>
            </div>
        </Link>
    );
});

TicketCard.displayName = 'TicketCard';
