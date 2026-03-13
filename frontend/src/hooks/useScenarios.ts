import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/api/client";
import type { ScenarioRequest, ScenarioResponse } from "@/types";

export function useScenarios() {
  return useQuery({
    queryKey: ["scenarios"],
    queryFn: api.getScenarios,
    staleTime: Infinity, // Scenarios don't change
  });
}

export function useRunScenario() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (request: ScenarioRequest) => api.runScenario(request),
    onSuccess: (data: ScenarioResponse) => {
      // Cache the scenario result
      queryClient.setQueryData(["scenario", data.scenario], data);
    },
  });
}
