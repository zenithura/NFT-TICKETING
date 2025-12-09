import React from 'react';
import { useTranslation } from 'react-i18next';
import { Zap, Shield, Users, Globe, Heart, TrendingUp } from 'lucide-react';

export const About: React.FC = React.memo(() => {
  const { t } = useTranslation();

  const features = [
    {
      icon: <Zap className="w-8 h-8" />,
      title: t('about.feature1.title', 'Blockchain Technology'),
      description: t('about.feature1.description', 'Secure and transparent NFT-based ticketing on Ethereum blockchain'),
    },
    {
      icon: <Shield className="w-8 h-8" />,
      title: t('about.feature2.title', 'Fraud Prevention'),
      description: t('about.feature2.description', 'Advanced ML-powered fraud detection and risk scoring'),
    },
    {
      icon: <Users className="w-8 h-8" />,
      title: t('about.feature3.title', 'Community Driven'),
      description: t('about.feature3.description', 'Built for event organizers, attendees, and resellers'),
    },
    {
      icon: <Globe className="w-8 h-8" />,
      title: t('about.feature4.title', 'Global Access'),
      description: t('about.feature4.description', 'Access events worldwide with decentralized infrastructure'),
    },
    {
      icon: <Heart className="w-8 h-8" />,
      title: t('about.feature5.title', 'Fair Resale Market'),
      description: t('about.feature5.description', '50% markup limit ensures fair pricing for everyone'),
    },
    {
      icon: <TrendingUp className="w-8 h-8" />,
      title: t('about.feature6.title', 'Future Proof'),
      description: t('about.feature6.description', 'Scalable platform ready for the next generation of events'),
    },
  ];

  return (
    <div className="max-w-6xl mx-auto space-y-16 animate-fade-in py-8">
      {/* Hero Section */}
      <div className="text-center space-y-6">
        <h1 className="text-5xl md:text-6xl font-bold tracking-tight text-foreground">
          {t('about.title', 'About NFTix')}
        </h1>
        <p className="text-xl text-foreground-secondary max-w-3xl mx-auto leading-relaxed">
          {t('about.subtitle', 'Revolutionizing event ticketing with blockchain technology, ensuring security, transparency, and fairness for all.')}
        </p>
      </div>

      {/* Mission Section */}
      <div className="bg-background-elevated rounded-2xl border border-border p-8 md:p-12">
        <h2 className="text-3xl font-bold text-foreground mb-6">
          {t('about.mission.title', 'Our Mission')}
        </h2>
        <p className="text-lg text-foreground-secondary leading-relaxed">
          {t('about.mission.description', 'NFTix is dedicated to transforming the event ticketing industry by leveraging blockchain technology to create a secure, transparent, and fair marketplace. We eliminate fraud, reduce scalping, and ensure that tickets remain accessible to genuine event enthusiasts.')}
        </p>
      </div>

      {/* Features Grid */}
      <div>
        <h2 className="text-3xl font-bold text-foreground mb-8 text-center">
          {t('about.whatWeOffer', 'What We Offer')}
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {features.map((feature, index) => (
            <div
              key={index}
              className="bg-background-elevated rounded-xl border border-border p-6 hover:border-primary/50 transition-all duration-200"
            >
              <div className="text-primary mb-4">{feature.icon}</div>
              <h3 className="text-xl font-semibold text-foreground mb-2">
                {feature.title}
              </h3>
              <p className="text-foreground-secondary">
                {feature.description}
              </p>
            </div>
          ))}
        </div>
      </div>

      {/* Values Section */}
      <div className="bg-background-elevated rounded-2xl border border-border p-8 md:p-12">
        <h2 className="text-3xl font-bold text-foreground mb-6">
          {t('about.values.title', 'Our Values')}
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <h3 className="text-xl font-semibold text-foreground mb-2">
              {t('about.values.transparency', 'Transparency')}
            </h3>
            <p className="text-foreground-secondary">
              {t('about.values.transparencyDesc', 'All transactions are recorded on the blockchain, providing complete transparency.')}
            </p>
          </div>
          <div>
            <h3 className="text-xl font-semibold text-foreground mb-2">
              {t('about.values.security', 'Security')}
            </h3>
            <p className="text-foreground-secondary">
              {t('about.values.securityDesc', 'Advanced fraud detection and blockchain security protect all users.')}
            </p>
          </div>
          <div>
            <h3 className="text-xl font-semibold text-foreground mb-2">
              {t('about.values.fairness', 'Fairness')}
            </h3>
            <p className="text-foreground-secondary">
              {t('about.values.fairnessDesc', 'Fair pricing policies ensure accessibility for all event-goers.')}
            </p>
          </div>
          <div>
            <h3 className="text-xl font-semibold text-foreground mb-2">
              {t('about.values.innovation', 'Innovation')}
            </h3>
            <p className="text-foreground-secondary">
              {t('about.values.innovationDesc', 'Cutting-edge technology drives the future of event ticketing.')}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
});

