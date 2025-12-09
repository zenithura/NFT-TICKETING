import React from 'react';
import { useTranslation } from 'react-i18next';
import {
  Shield,
  Zap,
  Users,
  Globe,
  Lock,
  TrendingUp,
  CheckCircle,
  Smartphone,
  BarChart3,
  Ticket,
  Wallet,
  Brain,
} from 'lucide-react';

export const Features: React.FC = React.memo(() => {
  const { t } = useTranslation();

  const mainFeatures = [
    {
      icon: <Ticket className="w-10 h-10" />,
      title: t('features.nftTickets.title', 'NFT-Based Tickets'),
      description: t('features.nftTickets.description', 'Unique, verifiable NFT tickets stored securely on the blockchain'),
      benefits: [
        t('features.nftTickets.benefit1', 'Immutable ownership records'),
        t('features.nftTickets.benefit2', 'Impossible to counterfeit'),
        t('features.nftTickets.benefit3', 'Transferable and tradable'),
      ],
    },
    {
      icon: <Shield className="w-10 h-10" />,
      title: t('features.fraudDetection.title', 'ML-Powered Fraud Detection'),
      description: t('features.fraudDetection.description', 'Advanced machine learning models detect and prevent fraudulent activities'),
      benefits: [
        t('features.fraudDetection.benefit1', 'Real-time risk scoring'),
        t('features.fraudDetection.benefit2', 'Behavioral analysis'),
        t('features.fraudDetection.benefit3', 'Automated threat detection'),
      ],
    },
    {
      icon: <TrendingUp className="w-10 h-10" />,
      title: t('features.fairResale.title', 'Fair Resale Market'),
      description: t('features.fairResale.description', '50% markup limit ensures fair pricing and prevents scalping'),
      benefits: [
        t('features.fairResale.benefit1', 'Transparent pricing'),
        t('features.fairResale.benefit2', 'Prevents excessive markups'),
        t('features.fairResale.benefit3', 'Protects buyers from scalpers'),
      ],
    },
    {
      icon: <Wallet className="w-10 h-10" />,
      title: t('features.web3Integration.title', 'Web3 Integration'),
      description: t('features.web3Integration.description', 'Seamless wallet connections and blockchain interactions'),
      benefits: [
        t('features.web3Integration.benefit1', 'MetaMask support'),
        t('features.web3Integration.benefit2', 'Manual wallet entry'),
        t('features.web3Integration.benefit3', 'Multi-chain ready'),
      ],
    },
    {
      icon: <Users className="w-10 h-10" />,
      title: t('features.multiRole.title', 'Multi-Role System'),
      description: t('features.multiRole.description', 'Support for buyers, organizers, resellers, and administrators'),
      benefits: [
        t('features.multiRole.benefit1', 'Organizer dashboards'),
        t('features.multiRole.benefit2', 'Buyer collections'),
        t('features.multiRole.benefit3', 'Admin controls'),
      ],
    },
    {
      icon: <BarChart3 className="w-10 h-10" />,
      title: t('features.analytics.title', 'Analytics & Insights'),
      description: t('features.analytics.description', 'Comprehensive KPIs and metrics for event performance'),
      benefits: [
        t('features.analytics.benefit1', 'Event statistics'),
        t('features.analytics.benefit2', 'Sales tracking'),
        t('features.analytics.benefit3', 'Performance metrics'),
      ],
    },
  ];

  const additionalFeatures = [
    {
      icon: <Lock className="w-6 h-6" />,
      text: t('features.additional.security', 'Blockchain Security'),
    },
    {
      icon: <Globe className="w-6 h-6" />,
      text: t('features.additional.global', 'Global Access'),
    },
    {
      icon: <Smartphone className="w-6 h-6" />,
      text: t('features.additional.mobile', 'Mobile Responsive'),
    },
    {
      icon: <Brain className="w-6 h-6" />,
      text: t('features.additional.ai', 'AI-Powered Analysis'),
    },
    {
      icon: <Zap className="w-6 h-6" />,
      text: t('features.additional.fast', 'Lightning Fast'),
    },
    {
      icon: <CheckCircle className="w-6 h-6" />,
      text: t('features.additional.verified', 'Verified Events'),
    },
  ];

  return (
    <div className="max-w-7xl mx-auto space-y-16 animate-fade-in py-8">
      {/* Header */}
      <div className="text-center space-y-6">
        <h1 className="text-5xl md:text-6xl font-bold tracking-tight text-foreground">
          {t('features.title', 'Platform Features')}
        </h1>
        <p className="text-xl text-foreground-secondary max-w-3xl mx-auto leading-relaxed">
          {t('features.subtitle', 'Discover the powerful features that make NFTix the leading NFT ticketing platform')}
        </p>
      </div>

      {/* Main Features Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {mainFeatures.map((feature, index) => (
          <div
            key={index}
            className="bg-background-elevated rounded-xl border border-border p-8 hover:border-primary/50 transition-all duration-200"
          >
            <div className="text-primary mb-4">{feature.icon}</div>
            <h2 className="text-2xl font-bold text-foreground mb-3">
              {feature.title}
            </h2>
            <p className="text-foreground-secondary mb-6 leading-relaxed">
              {feature.description}
            </p>
            <ul className="space-y-2">
              {feature.benefits.map((benefit, idx) => (
                <li key={idx} className="flex items-start gap-3">
                  <CheckCircle className="w-5 h-5 text-success flex-shrink-0 mt-0.5" />
                  <span className="text-foreground-secondary">{benefit}</span>
                </li>
              ))}
            </ul>
          </div>
        ))}
      </div>

      {/* Additional Features */}
      <div className="bg-background-elevated rounded-2xl border border-border p-8 md:p-12">
        <h2 className="text-3xl font-bold text-foreground mb-8 text-center">
          {t('features.additional.title', 'Additional Features')}
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {additionalFeatures.map((feature, index) => (
            <div
              key={index}
              className="flex items-center gap-4 p-4 rounded-lg bg-background border border-border hover:border-primary/50 transition-all duration-200"
            >
              <div className="text-primary flex-shrink-0">{feature.icon}</div>
              <span className="text-foreground font-medium">{feature.text}</span>
            </div>
          ))}
        </div>
      </div>

      {/* CTA Section */}
      <div className="text-center bg-gradient-to-br from-primary/10 to-primary/5 rounded-2xl border border-primary/20 p-12">
        <h2 className="text-3xl font-bold text-foreground mb-4">
          {t('features.cta.title', 'Ready to Get Started?')}
        </h2>
        <p className="text-lg text-foreground-secondary mb-8 max-w-2xl mx-auto">
          {t('features.cta.description', 'Join thousands of users who are already experiencing the future of event ticketing')}
        </p>
        <div className="flex flex-col sm:flex-row gap-4 justify-center">
          <a
            href="/"
            className="px-8 py-3 bg-primary hover:bg-primary-hover text-white font-semibold rounded-lg transition-all duration-200 inline-block"
          >
            {t('features.cta.browseEvents', 'Browse Events')}
          </a>
          <a
            href="/register"
            className="px-8 py-3 bg-background-elevated hover:bg-background-hover text-foreground border border-border font-semibold rounded-lg transition-all duration-200 inline-block"
          >
            {t('features.cta.getStarted', 'Get Started')}
          </a>
        </div>
      </div>
    </div>
  );
});

