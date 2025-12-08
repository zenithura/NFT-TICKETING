/**
 * LazyImage Component
 * Optimized image component with lazy loading, WebP support, and responsive images
 */

import React, { useState, useRef, useEffect } from 'react';

interface LazyImageProps extends React.ImgHTMLAttributes<HTMLImageElement> {
  src: string;
  srcSet?: string;
  sizes?: string;
  webpSrc?: string;
  webpSrcSet?: string;
  fallbackSrc?: string;
  placeholder?: string;
  dataCy?: string;
}

export const LazyImage: React.FC<LazyImageProps> = ({
  src,
  srcSet,
  sizes,
  webpSrc,
  webpSrcSet,
  fallbackSrc,
  placeholder,
  dataCy,
  className,
  alt = '',
  ...props
}) => {
  const [isLoaded, setIsLoaded] = useState(false);
  const [isInView, setIsInView] = useState(false);
  const [error, setError] = useState(false);
  const imgRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    // Use IntersectionObserver for lazy loading
    if (!imgRef.current) return;

    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            setIsInView(true);
            observer.disconnect();
          }
        });
      },
      {
        rootMargin: '50px', // Start loading 50px before image enters viewport
        threshold: 0.01,
      }
    );

    observer.observe(imgRef.current);

    return () => {
      observer.disconnect();
    };
  }, []);

  const handleLoad = () => {
    setIsLoaded(true);
  };

  const handleError = () => {
    setError(true);
    if (fallbackSrc) {
      setIsLoaded(true);
    }
  };

  // Use native lazy loading as fallback for modern browsers
  const loading = props.loading || 'lazy';

  return (
    <div
      ref={imgRef}
      className={`lazy-image-container ${className || ''}`}
      data-cy={dataCy}
      style={{ position: 'relative', overflow: 'hidden' }}
    >
      {/* Placeholder */}
      {!isLoaded && placeholder && (
        <div
          className="lazy-image-placeholder"
          style={{
            position: 'absolute',
            inset: 0,
            background: placeholder,
            backgroundSize: 'cover',
            filter: 'blur(10px)',
            transform: 'scale(1.1)',
          }}
        />
      )}

      {/* WebP source with fallback */}
      {isInView && (
        <picture>
          {webpSrc && (
            <source
              type="image/webp"
              srcSet={webpSrcSet || webpSrc}
              sizes={sizes}
            />
          )}
          <img
            src={error && fallbackSrc ? fallbackSrc : src}
            srcSet={srcSet}
            sizes={sizes}
            alt={alt}
            loading={loading}
            onLoad={handleLoad}
            onError={handleError}
            className={`lazy-image ${isLoaded ? 'loaded' : ''}`}
            style={{
              opacity: isLoaded ? 1 : 0,
              transition: 'opacity 0.3s ease-in-out',
              width: '100%',
              height: 'auto',
            }}
            {...props}
          />
        </picture>
      )}

      {/* Loading skeleton */}
      {!isInView && (
        <div
          className="lazy-image-skeleton"
          style={{
            width: '100%',
            aspectRatio: props.width && props.height ? `${props.width}/${props.height}` : '16/9',
            background: 'linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%)',
            backgroundSize: '200% 100%',
            animation: 'loading 1.5s infinite',
          }}
        />
      )}
    </div>
  );
};

