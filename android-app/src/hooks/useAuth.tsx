import React, {
  useState,
  useEffect,
  useCallback,
  createContext,
  useContext,
} from 'react';
import {authAPI, User} from '../api/auth';
import {storage} from '../utils/storage';

interface AuthContextType {
  user: User | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  register: (
    email: string,
    password: string,
    name: string,
    phone_number: string,
  ) => Promise<User>;
  isAuthenticated: boolean;
  isAdmin: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function useAuth(): AuthContextType {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}

interface AuthProviderProps {
  children: React.ReactNode;
}

export function AuthProvider({children}: AuthProviderProps): React.JSX.Element {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    checkAuth();
  }, []);

  const checkAuth = async () => {
    try {
      const sessionToken = await storage.getSessionToken();
      if (!sessionToken) {
        setLoading(false);
        return;
      }

      const userData = await authAPI.getCurrentUser(sessionToken);
      if (userData.roles && !Array.isArray(userData.roles)) {
        userData.roles = [];
      } else if (!userData.roles) {
        userData.roles = [];
      }
      setUser(userData);
    } catch (error) {
      console.error('Auth check failed:', error);
      await storage.clearSessionToken();
      await storage.clearUserData();
      setUser(null);
    } finally {
      setLoading(false);
    }
  };

  const login = useCallback(async (email: string, password: string) => {
    const response = await authAPI.login(email, password);

    if (response.session_token) {
      await storage.setSessionToken(response.session_token);
    }

    if (response.user.roles && !Array.isArray(response.user.roles)) {
      response.user.roles = [];
    } else if (!response.user.roles) {
      response.user.roles = [];
    }

    await storage.setUserData(response.user);
    setUser(response.user);
  }, []);

  const register = useCallback(
    async (
      email: string,
      password: string,
      name: string,
      phone_number: string,
    ): Promise<User> => {
      const response = await authAPI.register({
        email,
        password,
        name,
        phone_number,
      });
      return response.user;
    },
    [],
  );

  const logout = useCallback(async () => {
    try {
      const sessionToken = await storage.getSessionToken();
      if (sessionToken) {
        await authAPI.logout(sessionToken);
      }
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      await storage.clearSessionToken();
      await storage.clearUserData();
      setUser(null);
    }
  }, []);

  const isAuthenticated = !!user;
  const userRoles = user?.roles || [];
  const isAdmin = Array.isArray(userRoles) && userRoles.includes('admin');

  return (
    <AuthContext.Provider
      value={{
        user,
        loading,
        login,
        logout,
        register,
        isAuthenticated,
        isAdmin,
      }}>
      {children}
    </AuthContext.Provider>
  );
}
