import { useQuery } from "@tanstack/react-query";
import { api } from "@/api/client";

export function useHealth() {
  return useQuery({
    queryKey: ["health"],
    queryFn: api.health,
    refetchInterval: 30000, // Check every 30 seconds
    retry: 3,
  });
}

export function useHealthReady() {
  return useQuery({
    queryKey: ["health", "ready"],
    queryFn: api.healthReady,
    refetchInterval: 60000, // Check every minute
    retry: 3,
  });
}
