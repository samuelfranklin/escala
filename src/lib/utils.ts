import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";
import type { Event } from "$lib/types";

// Types expected by shadcn-svelte components (mirrored from bits-ui internals)
export type WithoutChild<T> = T extends { child?: any } ? Omit<T, "child"> : T;
export type WithoutChildren<T> = T extends { children?: any } ? Omit<T, "children"> : T;
export type WithoutChildrenOrChild<T> = WithoutChildren<WithoutChild<T>>;
export type WithElementRef<T, U extends HTMLElement = HTMLElement> = T & { ref?: U | null };

export function cn(...inputs: ClassValue[]) {
	return twMerge(clsx(inputs));
}

export function formatDateLong(dateStr: string): string {
	const [year, month, day] = dateStr.split('-').map(Number);
	const date = new Date(year, month - 1, day);
	return date.toLocaleDateString('pt-BR', { day: '2-digit', month: 'long', year: 'numeric' });
}

export function getNextEvent(events: Event[], today: string): Event | null {
	const upcoming = events
		.filter(e => e.event_date && e.event_date >= today)
		.sort((a, b) => (a.event_date ?? '').localeCompare(b.event_date ?? ''));
	return upcoming[0] ?? null;
}

export function maskPhone(value: string): string {
	const digits = value.replace(/\D/g, '').slice(0, 11);
	if (digits.length <= 2) return digits;
	if (digits.length <= 6) return `(${digits.slice(0, 2)}) ${digits.slice(2)}`;
	if (digits.length <= 10) return `(${digits.slice(0, 2)}) ${digits.slice(2, 6)}-${digits.slice(6)}`;
	return `(${digits.slice(0, 2)}) ${digits.slice(2, 7)}-${digits.slice(7)}`;
}
