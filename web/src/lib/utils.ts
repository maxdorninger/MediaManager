import { type ClassValue, clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';
import { env } from '$env/dynamic/public';
import { goto } from '$app/navigation';
import { base } from '$app/paths';
import { toast } from 'svelte-sonner';
// eslint-disable-next-line @typescript-eslint/no-explicit-any
export type WithoutChild<T> = T extends { child?: any } ? Omit<T, "child"> : T;
// eslint-disable-next-line @typescript-eslint/no-explicit-any
export type WithoutChildren<T> = T extends { children?: any } ? Omit<T, "children"> : T;
export type WithoutChildrenOrChild<T> = WithoutChildren<WithoutChild<T>>;
export type WithElementRef<T, U extends HTMLElement = HTMLElement> = T & { ref?: U | null };


const apiUrl = env.PUBLIC_API_URL;

export const qualityMap: { [key: number]: string } = {
	1: '4K/UHD',
	2: '1080p/FullHD',
	3: '720p/HD',
	4: '480p/SD',
	5: 'unknown'
};
export const torrentStatusMap: { [key: number]: string } = {
	1: 'finished',
	2: 'downloading',
	3: 'error',
	4: 'unknown'
};

export function cn(...inputs: ClassValue[]) {
	return twMerge(clsx(inputs));
}

export function getTorrentQualityString(value: number): string {
	return qualityMap[value] || 'unknown';
}

export function getTorrentStatusString(value: number): string {
	return torrentStatusMap[value] || 'unknown';
}

export function getFullyQualifiedMediaName(media: { name: string; year: number | null }): string {
	let name = media.name;
	if (media.year != null) {
		name += ' (' + media.year + ')';
	}
	return name;
}

export function convertTorrentSeasonRangeToIntegerRange(torrent: {
	season?: number[];
	seasons?: number[];
}): string {
	if (torrent?.season?.length === 1) return torrent.season[0]?.toString() || '';
	if (torrent?.season?.length && torrent.season.length >= 2) {
		const lastSeason = torrent.season.at(-1);
		return torrent.season[0]?.toString() + '-' + (lastSeason?.toString() || '');
	}
	if (torrent?.seasons?.length === 1) return torrent.seasons[0]?.toString() || '';
	if (torrent?.seasons?.length && torrent.seasons.length >= 2) {
		const lastSeason = torrent.seasons.at(-1);
		return torrent.seasons[0]?.toString() + '-' + (lastSeason?.toString() || '');
	} else {
		console.log('Error parsing season range: ' + torrent?.seasons + torrent?.season);
		return 'Error parsing season range: ' + torrent?.seasons + torrent?.season;
	}
}

export async function handleLogout() {
	const response = await fetch(apiUrl + '/auth/cookie/logout', {
		method: 'POST',
		credentials: 'include'
	});
	if (response.ok) {
		console.log('Logout successful!');
		toast.success('Logout successful!');
		await goto(base + '/login');
	} else {
		console.error('Logout failed:', response.status);
		toast.error('Logout failed: ' + response.status);
	}
}

export function formatSecondsToOptimalUnit(seconds: number): string {
	if (seconds < 0) return '0s';

	const units = [
		{ name: 'y', seconds: 365.25 * 24 * 60 * 60 }, // year (accounting for leap years)
		{ name: 'mo', seconds: 30.44 * 24 * 60 * 60 }, // month (average)
		{ name: 'd', seconds: 24 * 60 * 60 }, // day
		{ name: 'h', seconds: 60 * 60 }, // hour
		{ name: 'm', seconds: 60 }, // minute
		{ name: 's', seconds: 1 } // second
	];

	for (const unit of units) {
		const value = seconds / unit.seconds;
		if (value >= 1) {
			return `${Math.floor(value)}${unit.name}`;
		}
	}

	return '0s';
}
