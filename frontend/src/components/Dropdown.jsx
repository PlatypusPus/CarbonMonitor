import { useEffect, useId, useRef, useState } from "react";
import { Check, ChevronDown } from "lucide-react";

export default function Dropdown({ label, value, onChange, options, className = "" }) {
  const [open, setOpen] = useState(false);
  const root = useRef(null);
  const trigger = useRef(null);
  const menuId = useId();
  useEffect(() => {
    if (!open) return;
    const close = (event) => { if (!root.current?.contains(event.target)) setOpen(false); };
    document.addEventListener("pointerdown", close);
    root.current.querySelector('[aria-pressed="true"]')?.focus();
    return () => document.removeEventListener("pointerdown", close);
  }, [open]);
  return <div ref={root} className={`dropdown ${className}`} onBlur={(event) => {
    if (!event.currentTarget.contains(event.relatedTarget)) setOpen(false);
  }} onKeyDown={(event) => {
    if (event.key === "Escape") { setOpen(false); trigger.current.focus(); }
    if (open && ["ArrowDown", "ArrowUp", "Home", "End"].includes(event.key)) {
      event.preventDefault();
      const buttons = [...root.current.querySelectorAll('.dropdown-option')];
      const current = buttons.indexOf(document.activeElement);
      const next = event.key === "Home" ? 0 : event.key === "End" ? buttons.length - 1 : (current + (event.key === "ArrowDown" ? 1 : -1) + buttons.length) % buttons.length;
      buttons[next]?.focus();
    }
  }}>
    <button type="button" ref={trigger} aria-label={label} aria-expanded={open} aria-controls={menuId}
      className="dropdown-trigger" onClick={() => setOpen(!open)}>
      <span className="truncate">{options.find((option) => option.value === value)?.label || "Choose an option"}</span>
      <ChevronDown size={17} aria-hidden="true" className={`shrink-0 transition-transform ${open ? "rotate-180" : ""}`} />
    </button>
    {open && <div id={menuId} role="group" aria-label={label} className="dropdown-menu">
      <p className="px-3 pb-2 pt-1 text-xs font-semibold text-body">{label}</p>
      {options.map((option) => <button type="button" key={option.value} aria-pressed={option.value === value}
        className="dropdown-option" onClick={() => { onChange(option.value); setOpen(false); trigger.current.focus(); }}>
        <span>{option.label}</span>{option.value === value && <Check size={16} aria-hidden="true" className="shrink-0" />}
      </button>)}
    </div>}
  </div>;
}
