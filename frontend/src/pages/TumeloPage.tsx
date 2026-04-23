/**
 * tumeloramaphosa.com — Personal brand landing page
 * Positions Tumelo Ramaphosa as Africa's next AI billionaire
 */

import React, { useState, useEffect } from 'react';

const TumeloPage: React.FC = () => {
  const [email, setEmail] = useState('');
  const [submitted, setSubmitted] = useState(false);
  const [scrolled, setScrolled] = useState(false);

  // Handle scroll for navbar
  useEffect(() => {
    const handleScroll = () => setScrolled(window.scrollY > 50);
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    // TODO: Send to backend/Supabase
    setSubmitted(true);
    console.log('Contact form submitted:', email);
  };

  return (
    <div className="min-h-screen bg-black text-white overflow-x-hidden">
      {/* Navigation */}
      <nav
        className={`fixed top-0 w-full z-50 transition-all duration-300 ${
          scrolled ? 'bg-black/90 backdrop-blur-md border-b border-white/10' : 'bg-transparent'
        }`}
      >
        <div className="max-w-6xl mx-auto px-6 py-4 flex justify-between items-center">
          <div className="text-xl font-bold tracking-tight">TUMELO RAMAPHOSA</div>
          <div className="flex gap-6 text-sm text-gray-400">
            <a href="#about" className="hover:text-white transition">About</a>
            <a href="#mission" className="hover:text-white transition">Mission</a>
            <a href="#studex" className="hover:text-white transition">StudEx</a>
            <a href="#contact" className="hover:text-white transition">Contact</a>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="relative min-h-screen flex items-center justify-center px-6">
        {/* Animated gradient background */}
        <div className="absolute inset-0 bg-gradient-to-br from-purple-900/20 via-black to-blue-900/20" />
        <div className="absolute inset-0 opacity-30">
          <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-purple-600/30 rounded-full blur-3xl animate-pulse" />
          <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-blue-600/30 rounded-full blur-3xl animate-pulse delay-1000" />
        </div>

        <div className="relative z-10 text-center max-w-4xl mx-auto">
          <p className="text-purple-400 text-sm uppercase tracking-widest mb-4">
            Building Africa's AI Future
          </p>
          <h1 className="text-5xl md:text-7xl font-bold mb-6 leading-tight">
            Tumelo Ramaphosa
          </h1>
          <p className="text-xl md:text-2xl text-gray-400 mb-8 max-w-2xl mx-auto">
            AI Entrepreneur · Founder of StudEx · Building the next generation of
            autonomous business agents for Africa
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <a
              href="#studex"
              className="px-8 py-4 bg-white text-black font-semibold rounded-lg hover:bg-gray-200 transition"
            >
              Discover StudEx
            </a>
            <a
              href="#contact"
              className="px-8 py-4 border border-white/30 font-semibold rounded-lg hover:bg-white/10 transition"
            >
              Get in Touch
            </a>
          </div>
        </div>

        {/* Scroll indicator */}
        <div className="absolute bottom-10 left-1/2 -translate-x-1/2 animate-bounce">
          <svg className="w-6 h-6 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 14l-7 7m0 0l-7-7m7 7V3" />
          </svg>
        </div>
      </section>

      {/* About Section */}
      <section id="about" className="py-24 px-6 bg-gradient-to-b from-black to-gray-900">
        <div className="max-w-4xl mx-auto">
          <h2 className="text-3xl md:text-4xl font-bold mb-8">About</h2>
          <div className="prose prose-invert prose-lg text-gray-400">
            <p>
              I'm building the future of business automation in Africa. My mission is simple:
              democratize AI-powered tools so every entrepreneur — from Johannesburg to Lagos —
              can compete on a global scale.
            </p>
            <p>
              Currently developing <strong className="text-white">StudEx AI</strong>, an autonomous
              business agent that handles customer service, content creation, and operations 24/7.
              Think of it as having a full-time AI employee that never sleeps.
            </p>
            <p>
              I believe Africa doesn't need to copy Silicon Valley — we need to build our own
              solutions for our own markets. That means AI that speaks local languages, understands
              local context, and works on the infrastructure we actually have.
            </p>
          </div>

          {/* Stats */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-8 mt-16">
            <div className="text-center">
              <div className="text-3xl font-bold text-purple-400">9</div>
              <div className="text-sm text-gray-500 mt-1">AI Agents Built</div>
            </div>
            <div className="text-center">
              <div className="text-3xl font-bold text-blue-400">24/7</div>
              <div className="text-sm text-gray-500 mt-1">Automation</div>
            </div>
            <div className="text-center">
              <div className="text-3xl font-bold text-green-400">R0</div>
              <div className="text-sm text-gray-500 mt-1">Local Models</div>
            </div>
            <div className="text-center">
              <div className="text-3xl font-bold text-orange-400">100+</div>
              <div className="text-sm text-gray-500 mt-1">Leads/Day</div>
            </div>
          </div>
        </div>
      </section>

      {/* Mission Section */}
      <section id="mission" className="py-24 px-6 bg-gray-900">
        <div className="max-w-4xl mx-auto">
          <h2 className="text-3xl md:text-4xl font-bold mb-8">Mission</h2>
          <div className="space-y-6 text-gray-400">
            <div className="flex gap-4">
              <div className="w-12 h-12 rounded-lg bg-purple-600/20 flex items-center justify-center flex-shrink-0">
                <svg className="w-6 h-6 text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
              </div>
              <div>
                <h3 className="text-xl font-semibold text-white mb-2">Democratize AI</h3>
                <p>
                  Make enterprise-grade AI accessible to every African business — no PhD required,
                  no massive budgets needed.
                </p>
              </div>
            </div>

            <div className="flex gap-4">
              <div className="w-12 h-12 rounded-lg bg-blue-600/20 flex items-center justify-center flex-shrink-0">
                <svg className="w-6 h-6 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3.055 11H5a2 2 0 012 2v1a2 2 0 002 2 2 2 0 012 2v2.945M8 3.935V5.5A2.5 2.5 0 0010.5 8h.5a2 2 0 012 2 2 2 0 104 0 2 2 0 012-2h1.064M15 20.25a2.5 2.5 0 002.5-2.5V9a2.5 2.5 0 00-5 0v8.5" />
                </svg>
              </div>
              <div>
                <h3 className="text-xl font-semibold text-white mb-2">Build Local Solutions</h3>
                <p>
                  African markets have unique challenges. We build AI that understands local languages,
                  works on local infrastructure, and solves local problems.
                </p>
              </div>
            </div>

            <div className="flex gap-4">
              <div className="w-12 h-12 rounded-lg bg-green-600/20 flex items-center justify-center flex-shrink-0">
                <svg className="w-6 h-6 text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
                </svg>
              </div>
              <div>
                <h3 className="text-xl font-semibold text-white mb-2">Create Jobs</h3>
                <p>
                  AI won't replace humans — it will amplify them. We're building tools that let
                  small teams compete with corporations.
                </p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* StudEx Section */}
      <section id="studex" className="py-24 px-6 bg-gradient-to-b from-gray-900 to-black">
        <div className="max-w-4xl mx-auto">
          <h2 className="text-3xl md:text-4xl font-bold mb-8">StudEx AI</h2>
          <p className="text-xl text-gray-400 mb-12">
            An autonomous AI business agent that runs your customer service, content,
            and operations 24/7.
          </p>

          {/* Features Grid */}
          <div className="grid md:grid-cols-2 gap-6">
            <div className="p-6 rounded-xl border border-white/10 bg-white/5">
              <h3 className="text-lg font-semibold text-white mb-2">🤖 Customer Service Agent</h3>
              <p className="text-gray-400 text-sm">
                Handles 80%+ of customer queries automatically via WhatsApp, Slack, or Discord.
                Order status, returns, FAQs — all instant.
              </p>
            </div>

            <div className="p-6 rounded-xl border border-white/10 bg-white/5">
              <h3 className="text-lg font-semibold text-white mb-2">📝 Content Studio</h3>
              <p className="text-gray-400 text-sm">
                Generate social posts, ad copy, and email campaigns in your brand voice.
                What used to take hours now takes seconds.
              </p>
            </div>

            <div className="p-6 rounded-xl border border-white/10 bg-white/5">
              <h3 className="text-lg font-semibold text-white mb-2">📊 Analytics Dashboard</h3>
              <p className="text-gray-400 text-sm">
                Real-time insights into customer conversations, resolution rates, and
                satisfaction scores. Know exactly how your business is performing.
              </p>
            </div>

            <div className="p-6 rounded-xl border border-white/10 bg-white/5">
              <h3 className="text-lg font-semibold text-white mb-2">🔌 Multi-Platform</h3>
              <p className="text-gray-400 text-sm">
                Works on WhatsApp (20M+ SA users), Slack (B2B), Discord (communities),
                and web. Your customers choose where to chat.
              </p>
            </div>
          </div>

          {/* Pricing teaser */}
          <div className="mt-12 p-6 rounded-xl border border-purple-500/30 bg-purple-900/10">
            <div className="flex flex-col md:flex-row justify-between items-center gap-4">
              <div>
                <h3 className="text-lg font-semibold text-white">Starting at R2,500/month</h3>
                <p className="text-gray-400 text-sm">For e-commerce stores doing 100+ orders/month</p>
              </div>
              <a
                href="#contact"
                className="px-6 py-3 bg-purple-600 hover:bg-purple-700 text-white font-semibold rounded-lg transition"
              >
                Book a Demo
              </a>
            </div>
          </div>
        </div>
      </section>

      {/* Contact Section */}
      <section id="contact" className="py-24 px-6 bg-black">
        <div className="max-w-2xl mx-auto">
          <h2 className="text-3xl md:text-4xl font-bold mb-4">Get in Touch</h2>
          <p className="text-gray-400 mb-8">
            Interested in StudEx AI? Want to partner? Let's talk.
          </p>

          {submitted ? (
            <div className="p-6 rounded-xl bg-green-900/20 border border-green-500/30">
              <p className="text-green-400">Thanks! I'll get back to you within 24 hours.</p>
            </div>
          ) : (
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block text-sm text-gray-400 mb-2">Email</label>
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                  className="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-lg focus:outline-none focus:border-purple-500 text-white"
                  placeholder="you@company.com"
                />
              </div>
              <div>
                <label className="block text-sm text-gray-400 mb-2">Message</label>
                <textarea
                  rows={4}
                  required
                  className="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-lg focus:outline-none focus:border-purple-500 text-white resize-none"
                  placeholder="Tell me about your business or what you'd like to build..."
                />
              </div>
              <button
                type="submit"
                className="w-full px-6 py-4 bg-white text-black font-semibold rounded-lg hover:bg-gray-200 transition"
              >
                Send Message
              </button>
            </form>
          )}

          {/* Social links */}
          <div className="mt-12 flex gap-6 justify-center">
            <a
              href="https://linkedin.com/in/tumelo-ramaphosa"
              target="_blank"
              rel="noopener noreferrer"
              className="text-gray-500 hover:text-white transition"
            >
              <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 24 24">
                <path d="M19 0h-14c-2.761 0-5 2.239-5 5v14c0 2.761 2.239 5 5 5h14c2.762 0 5-2.239 5-5v-14c0-2.761-2.238-5-5-5zm-11 19h-3v-11h3v11zm-1.5-12.268c-.966 0-1.75-.79-1.75-1.764s.784-1.764 1.75-1.764 1.75.79 1.75 1.764-.783 1.764-1.75 1.764zm13.5 12.268h-3v-5.604c0-3.368-4-3.113-4 0v5.604h-3v-11h3v1.765c1.396-2.586 7-2.777 7 2.476v6.759z"/>
              </svg>
            </a>
            <a
              href="https://twitter.com/tumelo_ramaphosa"
              target="_blank"
              rel="noopener noreferrer"
              className="text-gray-500 hover:text-white transition"
            >
              <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 24 24">
                <path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"/>
              </svg>
            </a>
            <a
              href="mailto:tumelo@studex.ai"
              className="text-gray-500 hover:text-white transition"
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
              </svg>
            </a>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-8 px-6 border-t border-white/10">
        <div className="max-w-4xl mx-auto text-center text-gray-500 text-sm">
          <p>© 2026 Tumelo Ramaphosa. Building Africa's AI future.</p>
          <p className="mt-2">Johannesburg, South Africa</p>
        </div>
      </footer>
    </div>
  );
};

export default TumeloPage;
