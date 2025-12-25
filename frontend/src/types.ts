export enum CheckinStatus {
  DONE = "DONE",
  MISSED = "MISSED",
}

export interface User {
  id: number;
  email: string;
  username: string;
  created_at: string;
}

export interface Project {
  id: number;
  name: string;
  description: string | null;
  timezone: string;
  daily_reset_hour: number;
  creator_id: number;
  created_at: string;
  rules_locked: boolean;
}

export interface ProjectMember {
  id: number;
  username: string;
  joined_at: string;
}

export interface TodayStatus {
  user_id: number;
  username: string;
  status: CheckinStatus | null;
  checked_at: string | null;
}

export interface ProjectDetail extends Project {
  members: ProjectMember[];
  today_statuses: TodayStatus[];
}

export interface ProjectListItem {
  id: number;
  name: string;
  description: string | null;
  member_count: number;
  user_status_today: CheckinStatus | null;
}

export interface Checkin {
  id: number;
  user_id: number;
  project_id: number;
  date: string;
  status: CheckinStatus;
  checked_at: string | null;
  auto_marked: boolean;
}

export interface UserStreak {
  user_id: number;
  username: string;
  current_streak: number;
  longest_streak: number;
  total_checkins: number;
  total_days: number;
  consistency_percent: number;
}

export interface ProjectAnalytics {
  project_id: number;
  project_name: string;
  user_streaks: UserStreak[];
  total_project_days: number;
}

export interface UserAnalytics {
  user_id: number;
  username: string;
  project_id: number;
  checkins: Checkin[];
  current_streak: number;
  longest_streak: number;
  consistency_percent: number;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface LoginRequest {
  username: string;
  password: string;
}

export interface RegisterRequest {
  email: string;
  username: string;
  password: string;
}

export interface CreateProjectRequest {
  name: string;
  description?: string;
  timezone?: string;
  daily_reset_hour?: number;
}

export interface InviteResponse {
  id: number;
  project_id: number;
  code: string;
  created_at: string;
  expires_at: string | null;
  max_uses: number | null;
  current_uses: number;
}
