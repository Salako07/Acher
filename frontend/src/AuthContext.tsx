import { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { api } from './api';
import { User, LoginRequest, RegisterRequest } from './types';

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  login: (credentials: LoginRequest) => Promise<void>;
  register: (data: RegisterRequest) => Promise<void>;
  logout: () => void;
  loading: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    checkAuth();
  }, []);

  const checkAuth = async () => {
    const isAuth = api.isAuthenticated();
    if (isAuth) {
      try {
        const userData = await api.getMe();
        setUser(userData);
      } catch {
        api.clearTokens();
        setUser(null);
      }
    } else {
      setUser(null);
    }
    setLoading(false);
  };

  const login = async (credentials: LoginRequest) => {
    await api.login(credentials);
    const userData = await api.getMe();
    setUser(userData);
  };

  const register = async (data: RegisterRequest) => {
    await api.register(data);
  };

  const logout = () => {
    api.logout();
    setUser(null);
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        isAuthenticated: api.isAuthenticated(),
        login,
        register,
        logout,
        loading,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
}
