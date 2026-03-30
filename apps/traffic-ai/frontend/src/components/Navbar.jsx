import { NavLink } from 'react-router-dom';

const navItems = [
  { label: 'Dashboard', path: '/dashboard' },
  { label: 'Intersections', path: '/intersections' },
  { label: 'Emergency Mode', path: '/emergency' },
  { label: 'Legacy Dashboard', path: '/legacy' }
];

export default function Navbar() {
  return (
    <header className="sticky top-0 z-40 border-b border-white/10 bg-abyss/70 backdrop-blur-xl">
      <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-4">
        <div>
          <p className="text-xs uppercase tracking-[0.3em] text-white/50">
            Smart Traffic Integrated System
          </p>
          <h1 className="text-xl font-semibold text-white">
            Vehicle Analytics & Signal Management
          </h1>
        </div>
        <nav className="hidden items-center gap-6 text-sm font-medium text-white/70 md:flex">
          {navItems.map((item) => (
            <NavLink
              key={item.path}
              to={item.path}
              className={({ isActive }) =>
                `transition-colors hover:text-neon-cyan ${
                  isActive ? 'text-neon-cyan' : ''
                }`
              }
            >
              {item.label}
            </NavLink>
          ))}
        </nav>
        <div className="flex items-center gap-3 rounded-full border border-neon-cyan/30 bg-neon-cyan/10 px-4 py-2 text-xs font-semibold uppercase tracking-[0.2em] text-neon-cyan">
          <span className="h-2 w-2 animate-pulse rounded-full bg-neon-cyan" />
          System Monitor
        </div>
      </div>
      <div className="flex gap-4 overflow-x-auto border-t border-white/10 px-6 py-3 md:hidden">
        {navItems.map((item) => (
          <NavLink
            key={item.path}
            to={item.path}
            className={({ isActive }) =>
              `rounded-full px-4 py-2 text-xs font-semibold uppercase tracking-[0.2em] ${
                isActive
                  ? 'bg-neon-cyan/20 text-neon-cyan'
                  : 'bg-white/5 text-white/60'
              }`
            }
          >
            {item.label}
          </NavLink>
        ))}
      </div>
    </header>
  );
}
