/* eslint-disable @typescript-eslint/no-explicit-any */
import axios, { AxiosError } from "axios";
import { getCSRFToken } from "@/utils/csrf";

// Set base URL for the backend
const BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000"; // Replace with your actual backend URL

// Enable credentials (cookies like access_token and refresh_token)
const axiosInstance = axios.create({
  baseURL: BASE_URL,
  withCredentials: true,
  headers: {
    "Content-Type": "application/json",
  },
});

axiosInstance.interceptors.request.use((config) => {
  // Only add CSRF header to unsafe methods
  const csrfSafeMethod = /^(GET|HEAD|OPTIONS|TRACE)$/i;

  if (!csrfSafeMethod.test(config.method || "")) {
    const token = getCSRFToken();
    if (token) {
      config.headers["X-CSRFToken"] = token;
    }
  }

  return config;
});

let isRefreshing = false;
let failedQueue: any[] = [];

const processQueue = (error: any, token: string | null = null) => {
  failedQueue.forEach((prom) => {
    if (error) {
      prom.reject(error);
    } else {
      prom.resolve(token);
    }
  });

  failedQueue = [];
};

axiosInstance.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    // If access token expired and it's the first retry
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      if (isRefreshing) {
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject });
        })
          .then(() => axiosInstance(originalRequest))
          .catch((err) => Promise.reject(err));
      }

      isRefreshing = true;

      try {
        // Refresh the token
        await axiosInstance.get("/auth/updateAcessToken/");
        processQueue(null);
        return axiosInstance(originalRequest); // Retry original request
      } catch (refreshError) {
        processQueue(refreshError, null);

        if (typeof window !== "undefined") {
          window.location.href = "/signin";
        }

        return Promise.reject(refreshError);
      } finally {
        isRefreshing = false;
      }
    }

    return Promise.reject(error);
  }
);

// Interfaces
export interface RegisterData {
  username: string;
  email: string;
  password: string;
  password2: string;
}

export interface LoginData {
  username: string;
  password: string;
}

export interface UpdateUserPasswordData {
  email?: string;
  username?: string;
  password: string;
  newpassword: string;
  newpassword2: string;
}

export interface UpdateUserProfileData {
  email?: string;
  username?: string;
  password: string;
}

export interface ApiResponse<T> {
  success: boolean;
  data?: T;
  error?: string;
  message?: string;
}

// API Calls
export const registerUser = async (
  data: RegisterData
): Promise<ApiResponse<any>> => {
  try {
    const response = await axiosInstance.post("/auth/register/", data);
    return { success: true, data: response.data };
  } catch (error) {
    const axiosError = error as AxiosError;
    return {
      success: false,
      error:
        (axiosError.response?.data as { message?: string })?.message ||
        "Registration failed",
    };
  }
};

export const loginUser = async (data: LoginData): Promise<ApiResponse<any>> => {
  try {
    const response = await axiosInstance.post("/auth/login/", data);
    return { success: true, data: response.data };
  } catch (error) {
    const axiosError = error as AxiosError;
    return {
      success: false,
      error:
        (axiosError.response?.data as { message?: string })?.message ||
        "Login failed",
    };
  }
};

export const logoutUser = async (): Promise<ApiResponse<any>> => {
  try {
    const response = await axiosInstance.post("/auth/logout/");
    return { success: true, data: response.data };
  } catch (error) {
    const axiosError = error as AxiosError;
    return {
      success: false,
      error:
        (axiosError.response?.data as { message?: string })?.message ||
        "Logout failed",
    };
  }
};

export const getUsersList = async (): Promise<ApiResponse<any>> => {
  try {
    const response = await axiosInstance.get("/auth/users-list/");
    return { success: true, data: response.data };
  } catch (error) {
    const axiosError = error as AxiosError;
    return {
      success: false,
      error:
        (axiosError.response?.data as { message?: string })?.message ||
        "Failed to fetch users",
    };
  }
};

export const getUserDetail = async (
  userId: number
): Promise<ApiResponse<any>> => {
  try {
    const response = await axiosInstance.get(`/auth/users-list/${userId}/`);
    return { success: true, data: response.data };
  } catch (error) {
    const axiosError = error as AxiosError;
    return {
      success: false,
      error:
        (axiosError.response?.data as { message?: string })?.message ||
        "Failed to fetch user details",
    };
  }
};

export const updateUserPassword = async (
  data: UpdateUserPasswordData
): Promise<ApiResponse<any>> => {
  try {
    const response = await axiosInstance.post("/auth/update", data);
    return { success: true, data: response.data };
  } catch (error) {
    const axiosError = error as AxiosError;
    return {
      success: false,
      error:
        (axiosError.response?.data as { message?: string })?.message ||
        "Failed to update password",
    };
  }
};

export const updateAccessToken = async (): Promise<ApiResponse<any>> => {
  try {
    const response = await axiosInstance.get("/auth/updateAcessToken/");
    return { success: true, data: response.data };
  } catch (error) {
    const axiosError = error as AxiosError;
    return {
      success: false,
      error:
        (axiosError.response?.data as { message?: string })?.message ||
        "Failed to update access token",
    };
  }
};

export const getSelfDetail = async (): Promise<ApiResponse<any>> => {
  try {
    const response = await axiosInstance.get("/auth/me/");
    return { success: true, data: response.data };
  } catch (error) {
    const axiosError = error as AxiosError;
    return {
      success: false,
      error:
        (axiosError.response?.data as { message?: string })?.message ||
        "Failed to fetch user details",
    };
  }
};

export const updateUserProfile = async (
  data: UpdateUserProfileData
): Promise<ApiResponse<any>> => {
  try {
    const response = await axiosInstance.post("/auth/update-profile/", data);
    return { success: true, data: response.data };
  } catch (error) {
    const axiosError = error as AxiosError;
    return {
      success: false,
      error:
        (axiosError.response?.data as { message?: string })?.message ||
        "Failed to update profile",
    };
  }
};
