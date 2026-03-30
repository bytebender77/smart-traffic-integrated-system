import { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Search,
  Moon,
  Eye,
  Code2,
  MessageSquare,
  Monitor,
  Sparkles,
  ArrowUpRight,
  Zap,
  RefreshCw,
  GitCommit,
  Radio,
  Shield,
  Car,
  Siren,
  TrafficCone,
  MapPin,
  Activity,
  BarChart3,
  Cpu,
  Route,
  Timer,
  Waypoints,
  CircleDot,
} from 'lucide-react';

/* ─────────── Reusable Components ─────────── */

const FadeIn = ({ children, delay = 0, className = '' }) => {
  const [isVisible, setIsVisible] = useState(false);
  const domRef = useRef();

  useEffect(() => {
    const observer = new IntersectionObserver((entries) => {
      entries.forEach((entry) => setIsVisible(entry.isIntersecting));
    });
    const current = domRef.current;
    if (current) observer.observe(current);
    return () => current && observer.unobserve(current);
  }, []);

  return (
    <div
      ref={domRef}
      className={`transition-all duration-1000 ease-out transform ${
        isVisible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-10'
      } ${className}`}
      style={{ transitionDelay: `${delay}ms` }}
    >
      {children}
    </div>
  );
};

const FeatureCard = ({ name, desc, stars, icon: Icon, color = '#00b4ff' }) => (
  <div className="group relative bg-[#0d1117] border border-white/10 rounded-xl p-6 hover:border-blue-500/50 transition-all duration-300 hover:bg-[#161b22] cursor-pointer overflow-hidden">
    <div
      className="absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity"
      style={{
        background: `linear-gradient(135deg, ${color}08, transparent)`,
      }}
    />
    <div className="flex justify-between items-start mb-4 relative z-10">
      <h3 className="text-xl font-semibold text-white">{name}</h3>
      <div
        className="p-2 rounded-lg transition-colors"
        style={{
          background: `${color}10`,
        }}
      >
        <Icon size={20} style={{ color }} />
      </div>
    </div>
    <p className="text-gray-400 text-sm mb-6 line-clamp-2 relative z-10">{desc}</p>
    <div className="flex items-center gap-2 text-sm relative z-10" style={{ color }}>
      <Activity size={14} />
      {stars}
    </div>
  </div>
);

const FeatureItem = ({ icon: Icon, title, desc }) => (
  <div className="flex flex-col gap-3">
    <div className="w-10 h-10 rounded-lg bg-[#1a1f2e] border border-white/5 flex items-center justify-center text-blue-400 mb-2">
      <Icon size={20} />
    </div>
    <h3 className="text-lg font-medium text-white">{title}</h3>
    <p className="text-gray-400 text-sm leading-relaxed">{desc}</p>
  </div>
);

/* ─────────── Landing Page ─────────── */

export default function LandingPage() {
  const [scrollY, setScrollY] = useState(0);
  const navigate = useNavigate();

  useEffect(() => {
    const handleScroll = () => setScrollY(window.scrollY);
    window.addEventListener('scroll', handleScroll, { passive: true });
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  const rotateX = scrollY * 0.05;
  const rotateY = scrollY * 0.1;
  const scale = Math.max(0.5, 1 - scrollY * 0.0005);
  const opacity = Math.max(0, 1 - scrollY * 0.002);

  return (
    <div className="min-h-screen bg-black text-white font-sans selection:bg-blue-500/30 overflow-x-hidden">
      {/* ── Navigation ── */}
      <nav className="fixed top-0 left-0 right-0 z-50 flex items-center justify-between px-6 py-4 bg-black/50 backdrop-blur-md border-b border-white/5">
        <div className="flex items-center gap-2">
          <div className="w-7 h-7 rounded-md flex items-center justify-center"
            style={{ background: 'linear-gradient(135deg, #00b4ff, #00ff87)' }}>
            <Radio size={14} className="text-black" />
          </div>
          <span className="font-semibold tracking-tight" style={{ fontFamily: "'Orbitron', sans-serif" }}>
            SMART TRAFFIC SYSTEM
          </span>
        </div>
        <div className="hidden md:flex items-center bg-[#161b22] border border-white/10 rounded-full px-4 py-2 w-96">
          <Search size={16} className="text-gray-500 mr-2" />
          <input
            type="text"
            placeholder="Search intersections, signals, routes..."
            className="bg-transparent border-none outline-none text-sm w-full placeholder-gray-500 text-white"
          />
        </div>
        <button
          onClick={() => navigate('/dashboard')}
          className="flex items-center gap-2 bg-white/10 hover:bg-white/15 px-4 py-2 rounded-full text-sm font-medium transition-colors"
        >
          Judges Showcase
          <ArrowUpRight size={16} />
        </button>
      </nav>

      {/* ── Hero Section ── */}
      <section className="relative min-h-screen flex flex-col items-center justify-center pt-20 overflow-hidden">
        {/* Background glow */}
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] rounded-full blur-[120px] pointer-events-none"
          style={{ background: 'radial-gradient(circle, rgba(0,180,255,0.2), rgba(0,255,135,0.08), transparent)' }} />

        <div className="z-10 text-center px-4 mb-12">
          <div className="inline-flex items-center gap-2 bg-white/5 border border-white/10 rounded-full px-4 py-1.5 mb-8 text-sm text-gray-400">
            <Sparkles size={14} className="text-blue-400" />
            AI-Powered Smart City Infrastructure
          </div>
          <h1 className="text-6xl md:text-8xl font-bold tracking-tighter mb-6 bg-clip-text text-transparent bg-gradient-to-b from-white to-white/50"
            style={{ fontFamily: "'Orbitron', sans-serif" }}>
            Traffic Intelligence AI
          </h1>
          <p className="text-xl text-blue-200/80 max-w-2xl mx-auto font-light leading-relaxed">
            Dynamic Traffic Flow Optimizer & Emergency Grid. <br />
            Computer vision meets real-time signal intelligence.
          </p>
          <div className="flex items-center justify-center gap-4 mt-10">
            <button
              onClick={() => navigate('/dashboard')}
              className="group flex items-center gap-3 bg-white text-black px-7 py-3.5 rounded-full font-semibold hover:bg-gray-200 transition-colors"
            >
              <Zap size={18} className="text-blue-600" />
              Launch Control Center
              <ArrowUpRight size={18} className="group-hover:translate-x-1 group-hover:-translate-y-1 transition-transform" />
            </button>
            <button
              onClick={() => navigate('/emergency')}
              className="flex items-center gap-2 border border-red-500/30 text-red-400 hover:bg-red-500/10 px-6 py-3.5 rounded-full font-medium transition-colors"
            >
              <Siren size={18} />
              Emergency Mode
            </button>
          </div>
        </div>

        {/* 3D Cube Visual */}
        <div
          className="relative w-64 h-64 md:w-80 md:h-80"
          style={{
            transform: `perspective(1000px) rotateX(${rotateX}deg) rotateY(${rotateY}deg) scale(${scale})`,
            opacity,
            transformStyle: 'preserve-3d',
            transition: 'transform 0.1s ease-out',
          }}
        >
          {[
            { tz: 128, ry: 0, icon: Car, color: '#00b4ff' },
            { tz: 128, ry: 180, icon: Siren, color: '#ff3b5c' },
            { tz: 128, ry: 90, icon: TrafficCone, color: '#ffd600' },
            { tz: 128, ry: -90, icon: MapPin, color: '#00ff87' },
            { tz: 128, rx: 90, icon: Activity, color: '#a855f7' },
            { tz: 128, rx: -90, icon: Eye, color: '#22d3ee' },
          ].map((face, i) => {
            let t = '';
            if (face.ry !== undefined && face.ry !== 0) t += `rotateY(${face.ry}deg) `;
            if (face.rx !== undefined) t += `rotateX(${face.rx}deg) `;
            t += `translateZ(${face.tz}px)`;
            return (
              <div
                key={i}
                className="absolute inset-0 border backdrop-blur-sm flex items-center justify-center"
                style={{
                  transform: t,
                  backfaceVisibility: 'visible',
                  borderColor: `${face.color}40`,
                  background: `${face.color}08`,
                }}
              >
                <face.icon className="w-16 h-16 md:w-20 md:h-20" style={{ color: `${face.color}60` }} strokeWidth={1} />
              </div>
            );
          })}
        </div>

        {/* Mobile search */}
        <div className="md:hidden mt-12 w-full max-w-sm px-6">
          <div className="flex items-center bg-[#161b22] border border-white/10 rounded-full px-4 py-3">
            <Search size={18} className="text-gray-500 mr-2" />
            <input
              type="text"
              placeholder="Search intersections..."
              className="bg-transparent border-none outline-none text-sm w-full placeholder-gray-500 text-white"
            />
          </div>
        </div>
      </section>

      {/* ── Core Capabilities ── */}
      <section className="py-24 px-6 max-w-7xl mx-auto">
        <FadeIn>
          <h2 className="text-3xl md:text-4xl font-semibold mb-4" style={{ fontFamily: "'Orbitron', sans-serif" }}>
            Core Capabilities
          </h2>
          <p className="text-gray-400 mb-12 max-w-xl">Every component of the system working together to build a safer, smarter city.</p>
        </FadeIn>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          <FadeIn delay={100}>
            <FeatureCard
              name="Vehicle Detection"
              desc="YOLOv8-powered computer vision detects cars, buses, trucks, and bikes in real-time from camera feeds."
              stars="Real-Time CV"
              icon={Eye}
              color="#00b4ff"
            />
          </FadeIn>
          <FadeIn delay={200}>
            <FeatureCard
              name="Signal Optimization"
              desc="AI-driven algorithm calculates optimal green/red durations based on live traffic density and queue length."
              stars="Heuristic AI"
              icon={Timer}
              color="#00ff87"
            />
          </FadeIn>
          <FadeIn delay={300}>
            <FeatureCard
              name="Emergency Green Corridor"
              desc="Instant detection of ambulances and fire trucks triggers a green wave along the fastest route to the hospital."
              stars="Priority Routing"
              icon={Siren}
              color="#ff3b5c"
            />
          </FadeIn>
          <FadeIn delay={400}>
            <FeatureCard
              name="Traffic Density Mapping"
              desc="Live congestion heatmaps across all intersections with color-coded density levels: low, medium, high."
              stars="Live Heatmap"
              icon={BarChart3}
              color="#ffd600"
            />
          </FadeIn>
          <FadeIn delay={500}>
            <FeatureCard
              name="Smart Intersections"
              desc="Each intersection reports vehicle count, density percentage, and signal state to the central control system."
              stars="8 Active Nodes"
              icon={Waypoints}
              color="#a855f7"
            />
          </FadeIn>
          <FadeIn delay={600}>
            <FeatureCard
              name="City Command Center"
              desc="Unified dashboard for city administrators to monitor, control, and override the entire traffic grid."
              stars="Full Control"
              icon={Monitor}
              color="#22d3ee"
            />
          </FadeIn>
        </div>
      </section>

      {/* ── How It Works (CTA Section) ── */}
      <section className="py-24 px-6 relative overflow-hidden">
        <div className="max-w-7xl mx-auto grid md:grid-cols-2 gap-12 items-center">
          <FadeIn>
            <div>
              <div className="flex items-center gap-4 mb-6">
                <h2 className="text-4xl md:text-5xl font-semibold" style={{ fontFamily: "'Orbitron', sans-serif" }}>
                  See it in action
                </h2>
                <span className="px-3 py-1 rounded-full border border-green-500/30 text-xs font-medium text-green-400 whitespace-nowrap">
                  Live Preview
                </span>
              </div>
              <p className="text-gray-400 text-lg mb-8 leading-relaxed">
                Upload a traffic video. Watch the AI detect every vehicle in real-time. See signal timings adjust automatically.
                Introduce an ambulance — and watch the green corridor activate instantly.
              </p>
              <button
                onClick={() => navigate('/dashboard')}
                className="group flex items-center gap-3 bg-white text-black px-6 py-3 rounded-full font-medium hover:bg-gray-200 transition-colors"
              >
                <Sparkles size={18} className="text-blue-600" />
                Open Control Center
                <ArrowUpRight size={18} className="group-hover:translate-x-1 group-hover:-translate-y-1 transition-transform" />
              </button>
            </div>
          </FadeIn>

          <FadeIn delay={200} className="relative">
            <div className="relative w-full aspect-square max-w-md mx-auto">
              <div className="absolute inset-0 bg-gradient-to-tr from-blue-600/20 to-green-600/15 rounded-full blur-3xl" />
              <div className="relative z-10 w-full h-full border border-white/10 rounded-2xl bg-[#0d1117]/80 backdrop-blur-xl p-6 shadow-2xl overflow-hidden">
                <div className="absolute inset-0 opacity-20 font-mono text-xs text-blue-300 p-4 overflow-hidden whitespace-pre leading-relaxed">
                  {`// Vehicle Detection Pipeline
async function detectVehicles(frame) {
  const detections = await yolov8.predict(frame);
  const counts = {
    cars: 0, buses: 0, trucks: 0, bikes: 0
  };
  
  detections.forEach(d => {
    counts[d.class]++;
    drawBoundingBox(frame, d.bbox, d.class);
  });

  return { counts, density: calcDensity(counts) };
}

// Signal Optimization
function optimizeSignal(density) {
  const greenTime = BASE_TIME * (density / 100);
  return Math.min(MAX_GREEN, Math.max(MIN_GREEN,
    greenTime));
}`}
                </div>
                {/* Glowing cube overlay */}
                <div
                  className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-32 h-32 backdrop-blur-md transform rotate-12 hover:rotate-45 transition-transform duration-700"
                  style={{
                    border: '1px solid rgba(0,255,135,0.4)',
                    background: 'rgba(0,255,135,0.06)',
                  }}
                />
              </div>
            </div>
          </FadeIn>
        </div>
      </section>

      {/* ── Features Grid ── */}
      <section className="py-24 px-6 max-w-7xl mx-auto">
        <div className="grid md:grid-cols-2 gap-16 items-center">
          <FadeIn>
            <div className="space-y-8">
              <h2 className="text-4xl md:text-5xl font-semibold leading-tight" style={{ fontFamily: "'Orbitron', sans-serif" }}>
                Intelligent traffic <br />
                <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-green-400">
                  for smarter cities
                </span>
              </h2>
              <p className="text-gray-400 text-lg">
                Every intersection optimized. Every emergency response accelerated.
              </p>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-8 pt-8">
                <FeatureItem
                  icon={Eye}
                  title="Real-Time Vehicle Detection"
                  desc="YOLOv8 detects and classifies every vehicle — cars, buses, trucks, bikes — with bounding-box overlays."
                />
                <FeatureItem
                  icon={Zap}
                  title="Dynamic Signal Timing"
                  desc="Green time auto-adjusts proportional to traffic density. High-density lanes get priority."
                />
                <FeatureItem
                  icon={Route}
                  title="Green Corridor Routing"
                  desc="Emergency vehicles trigger instant green waves along the fastest path to their destination."
                />
                <FeatureItem
                  icon={RefreshCw}
                  title="Always Monitoring"
                  desc="24/7 surveillance across all intersections with live density estimation and congestion alerts."
                />
              </div>
            </div>
          </FadeIn>

          <FadeIn delay={200} className="relative">
            <div className="relative w-full aspect-square">
              <div className="absolute inset-0 bg-blue-600/10 rounded-full blur-3xl" />
              <div className="relative z-10 w-full h-full flex items-center justify-center">
                <div className="w-64 h-64 border border-white/10 rounded-xl bg-[#161b22] relative">
                  <div className="absolute -top-4 -left-4 w-24 h-24 border border-blue-500/30 bg-blue-500/5 rounded-lg flex items-center justify-center">
                    <Car size={28} className="text-blue-400/60" />
                  </div>
                  <div className="absolute -bottom-4 -right-4 w-32 h-32 border border-green-500/30 bg-green-500/5 rounded-lg flex items-center justify-center">
                    <Siren size={32} className="text-green-400/60" />
                  </div>
                  <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-20 h-20 border border-white/20 bg-white/5 rounded-full flex items-center justify-center">
                    <div className="w-3 h-3 bg-green-400 rounded-full animate-pulse" />
                  </div>
                  <svg className="absolute inset-0 w-full h-full pointer-events-none stroke-white/10" style={{ overflow: 'visible' }}>
                    <line x1="0" y1="0" x2="50%" y2="50%" />
                    <line x1="100%" y1="100%" x2="50%" y2="50%" />
                  </svg>
                </div>
              </div>
            </div>
          </FadeIn>
        </div>
      </section>

      {/* ── Emergency System Section ── */}
      <section className="py-24 px-6 bg-[#0a0a0a]">
        <div className="max-w-7xl mx-auto grid md:grid-cols-2 gap-16 items-center">
          <FadeIn className="order-2 md:order-1 relative">
            <div className="relative w-full aspect-video bg-[#0d1117] rounded-xl border border-white/10 overflow-hidden shadow-2xl">
              {/* Emergency UI Mockup */}
              <div className="absolute top-0 left-0 right-0 h-12 bg-[#161b22] border-b border-white/5 flex items-center px-4 gap-2">
                <div className="w-3 h-3 rounded-full bg-red-500/50 animate-pulse" />
                <div className="w-3 h-3 rounded-full bg-yellow-500/20" />
                <div className="w-3 h-3 rounded-full bg-green-500/20" />
                <span className="ml-2 text-xs text-red-400 font-semibold" style={{ fontFamily: "'Orbitron', sans-serif" }}>
                  EMERGENCY ACTIVE
                </span>
              </div>
              <div className="p-6 pt-16 space-y-4">
                <div className="flex gap-3">
                  <div className="w-8 h-8 rounded-full bg-red-500/20 flex-shrink-0 flex items-center justify-center">
                    <Siren size={14} className="text-red-400" />
                  </div>
                  <div className="bg-red-500/10 rounded-lg rounded-tl-none p-3 text-sm text-gray-300 border border-red-500/20">
                    🚨 Ambulance detected at <span className="text-red-400">Koramangala Junction</span> heading towards St. John's Hospital
                  </div>
                </div>
                <div className="flex gap-3 flex-row-reverse">
                  <div className="w-8 h-8 rounded-full bg-green-500/20 flex-shrink-0 flex items-center justify-center">
                    <Shield size={14} className="text-green-400" />
                  </div>
                  <div className="bg-green-500/10 rounded-lg rounded-tr-none p-3 text-sm text-gray-300 border border-green-500/20">
                    ✅ Green corridor activated — <span className="text-green-400">INT-002 → INT-006 → INT-008</span> set to GREEN. ETA: 4 min.
                  </div>
                </div>
              </div>
            </div>
          </FadeIn>

          <FadeIn delay={200} className="order-1 md:order-2">
            <h2 className="text-4xl md:text-5xl font-semibold mb-6" style={{ fontFamily: "'Orbitron', sans-serif" }}>
              Saving lives, <br />one green light at a time
            </h2>
            <p className="text-gray-400 text-lg mb-10">
              When every second counts, our AI creates an instant green corridor. Emergency vehicles reach their destination faster — with zero red lights in their path.
            </p>

            <div className="space-y-6">
              {[
                { icon: Siren, text: 'Automatic emergency vehicle detection', color: '#ff3b5c' },
                { icon: Route, text: 'Fastest-path green corridor generation', color: '#00ff87' },
                { icon: Timer, text: 'Real-time ETA & signal coordination', color: '#00b4ff' },
              ].map((item, i) => (
                <div key={i} className="flex items-center gap-4 group cursor-pointer">
                  <div
                    className="w-10 h-10 rounded-lg border border-white/5 flex items-center justify-center transition-all"
                    style={{ background: `${item.color}10` }}
                  >
                    <item.icon size={20} style={{ color: item.color }} />
                  </div>
                  <span className="text-lg font-medium text-gray-300 group-hover:text-white transition-colors">
                    {item.text}
                  </span>
                </div>
              ))}
            </div>
          </FadeIn>
        </div>
      </section>

      {/* ── Final CTA ── */}
      <section className="py-32 px-6 text-center relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-b from-black via-blue-950/20 to-black pointer-events-none" />
        <FadeIn>
          <h2 className="text-4xl md:text-6xl font-bold mb-4 tracking-tight" style={{ fontFamily: "'Orbitron', sans-serif" }}>
            The future of urban <br /> traffic management
          </h2>
          <p className="text-gray-400 text-lg mb-10 max-w-xl mx-auto">
            Reduced congestion. Optimized signals. Faster emergency response. All powered by AI.
          </p>
          <div className="relative inline-block">
            <div className="absolute inset-0 bg-blue-500 blur-2xl opacity-20" />
            <button
              onClick={() => navigate('/dashboard')}
              className="relative bg-[#161b22] border border-white/10 hover:border-blue-500/50 text-white px-8 py-4 rounded-full font-medium transition-all hover:scale-105 flex items-center gap-3 mx-auto"
            >
              <Sparkles className="text-blue-400" size={20} />
              Enter the Control Center
              <ArrowUpRight size={18} />
            </button>
          </div>
        </FadeIn>
      </section>

      {/* ── Footer ── */}
      <footer className="border-t border-white/10 py-12 px-6 bg-black">
        <div className="max-w-7xl mx-auto flex flex-col md:flex-row justify-between items-center gap-6">
          <div className="flex items-center gap-2 text-gray-500">
            <div className="w-5 h-5 rounded-sm flex items-center justify-center"
              style={{ background: 'linear-gradient(135deg, #00b4ff, #00ff87)' }}>
              <Radio size={10} className="text-black" />
            </div>
            <span className="font-medium">Vehicle Analytics & Signal Management</span>
          </div>
          <div className="flex gap-8 text-sm text-gray-500">
            <a href="#" className="hover:text-white transition-colors">Dashboard</a>
            <a href="#" className="hover:text-white transition-colors">Documentation</a>
            <a href="#" className="hover:text-white transition-colors">Team</a>
            <a href="#" className="hover:text-white transition-colors">About</a>
          </div>
        </div>
      </footer>
    </div>
  );
}
