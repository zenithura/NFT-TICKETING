import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Mail, MessageSquare, Send, CheckCircle } from 'lucide-react';
import { toast } from 'react-hot-toast';

export const Contact: React.FC = React.memo(() => {
  const { t } = useTranslation();
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    subject: '',
    message: '',
  });
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isSubmitted, setIsSubmitted] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);

    // Simulate form submission (replace with actual API call)
    try {
      await new Promise(resolve => setTimeout(resolve, 1000));
      setIsSubmitted(true);
      toast.success(t('contact.success', 'Message sent successfully!'));
      setFormData({ name: '', email: '', subject: '', message: '' });
      setTimeout(() => setIsSubmitted(false), 3000);
    } catch (error) {
      toast.error(t('contact.error', 'Failed to send message. Please try again.'));
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    setFormData(prev => ({
      ...prev,
      [e.target.name]: e.target.value,
    }));
  };

  return (
    <div className="max-w-4xl mx-auto space-y-12 animate-fade-in py-8">
      {/* Header */}
      <div className="text-center space-y-4">
        <h1 className="text-5xl md:text-6xl font-bold tracking-tight text-foreground">
          {t('contact.title', 'Contact Us')}
        </h1>
        <p className="text-xl text-foreground-secondary max-w-2xl mx-auto">
          {t('contact.subtitle', 'Have a question or feedback? We\'d love to hear from you!')}
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Contact Information */}
        <div className="space-y-6">
          <div className="bg-background-elevated rounded-xl border border-border p-6">
            <h2 className="text-2xl font-bold text-foreground mb-6">
              {t('contact.getInTouch', 'Get in Touch')}
            </h2>
            <div className="space-y-4">
              <div className="flex items-start gap-4">
                <div className="p-3 bg-primary/10 rounded-lg text-primary">
                  <Mail className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="font-semibold text-foreground mb-1">
                    {t('contact.email', 'Email')}
                  </h3>
                  <a
                    href="mailto:support@nftix.com"
                    className="text-foreground-secondary hover:text-primary transition-colors"
                  >
                    support@nftix.com
                  </a>
                </div>
              </div>
              <div className="flex items-start gap-4">
                <div className="p-3 bg-primary/10 rounded-lg text-primary">
                  <MessageSquare className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="font-semibold text-foreground mb-1">
                    {t('contact.support', 'Support')}
                  </h3>
                  <p className="text-foreground-secondary">
                    {t('contact.supportHours', 'Available 24/7 via email')}
                  </p>
                </div>
              </div>
            </div>
          </div>

          <div className="bg-background-elevated rounded-xl border border-border p-6">
            <h3 className="text-xl font-semibold text-foreground mb-4">
              {t('contact.whyContact', 'Why Contact Us?')}
            </h3>
            <ul className="space-y-2 text-foreground-secondary">
              <li>• {t('contact.reason1', 'Report issues or bugs')}</li>
              <li>• {t('contact.reason2', 'Suggest new features')}</li>
              <li>• {t('contact.reason3', 'Request event partnerships')}</li>
              <li>• {t('contact.reason4', 'Get technical support')}</li>
              <li>• {t('contact.reason5', 'Provide feedback')}</li>
            </ul>
          </div>
        </div>

        {/* Contact Form */}
        <div className="bg-background-elevated rounded-xl border border-border p-6">
          <h2 className="text-2xl font-bold text-foreground mb-6">
            {t('contact.sendMessage', 'Send us a Message')}
          </h2>
          {isSubmitted ? (
            <div className="text-center py-12">
              <CheckCircle className="w-16 h-16 text-success mx-auto mb-4" />
              <p className="text-lg font-semibold text-foreground mb-2">
                {t('contact.thanks', 'Thank you!')}
              </p>
              <p className="text-foreground-secondary">
                {t('contact.willRespond', 'We\'ll get back to you soon.')}
              </p>
            </div>
          ) : (
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label htmlFor="name" className="block text-sm font-medium text-foreground mb-2">
                  {t('contact.name', 'Name')}
                </label>
                <input
                  type="text"
                  id="name"
                  name="name"
                  value={formData.name}
                  onChange={handleChange}
                  required
                  className="w-full bg-background border border-border rounded-lg px-4 py-2 text-foreground focus:border-primary focus:ring-2 focus:ring-primary/20 transition-colors"
                />
              </div>
              <div>
                <label htmlFor="email" className="block text-sm font-medium text-foreground mb-2">
                  {t('contact.email', 'Email')}
                </label>
                <input
                  type="email"
                  id="email"
                  name="email"
                  value={formData.email}
                  onChange={handleChange}
                  required
                  className="w-full bg-background border border-border rounded-lg px-4 py-2 text-foreground focus:border-primary focus:ring-2 focus:ring-primary/20 transition-colors"
                />
              </div>
              <div>
                <label htmlFor="subject" className="block text-sm font-medium text-foreground mb-2">
                  {t('contact.subject', 'Subject')}
                </label>
                <input
                  type="text"
                  id="subject"
                  name="subject"
                  value={formData.subject}
                  onChange={handleChange}
                  required
                  className="w-full bg-background border border-border rounded-lg px-4 py-2 text-foreground focus:border-primary focus:ring-2 focus:ring-primary/20 transition-colors"
                />
              </div>
              <div>
                <label htmlFor="message" className="block text-sm font-medium text-foreground mb-2">
                  {t('contact.message', 'Message')}
                </label>
                <textarea
                  id="message"
                  name="message"
                  value={formData.message}
                  onChange={handleChange}
                  required
                  rows={6}
                  className="w-full bg-background border border-border rounded-lg px-4 py-2 text-foreground focus:border-primary focus:ring-2 focus:ring-primary/20 transition-colors resize-none"
                />
              </div>
              <button
                type="submit"
                disabled={isSubmitting}
                className="w-full bg-primary hover:bg-primary-hover text-white font-semibold py-3 rounded-lg transition-all duration-200 flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isSubmitting ? (
                  <>
                    <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                    {t('contact.sending', 'Sending...')}
                  </>
                ) : (
                  <>
                    <Send className="w-5 h-5" />
                    {t('contact.send', 'Send Message')}
                  </>
                )}
              </button>
            </form>
          )}
        </div>
      </div>
    </div>
  );
});

