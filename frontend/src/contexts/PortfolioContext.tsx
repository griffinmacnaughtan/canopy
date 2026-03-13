import { createContext, useContext, useState, useCallback, useEffect, ReactNode } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/api/client";
import type { PortfolioSummary, Asset } from "@/types";

interface PortfolioContextType {
  selectedPortfolioId: string | undefined;
  setSelectedPortfolioId: (id: string) => void;
  portfolios: PortfolioSummary[];
  isLoading: boolean;
  error: Error | null;
  createPortfolio: (name: string, assets: Asset[]) => Promise<string>;
  isCreating: boolean;
}

const PortfolioContext = createContext<PortfolioContextType | undefined>(undefined);

interface PortfolioProviderProps {
  children: ReactNode;
}

export function PortfolioProvider({ children }: PortfolioProviderProps) {
  const [selectedPortfolioId, setSelectedPortfolioIdState] = useState<string | undefined>(undefined);
  const [isCreating, setIsCreating] = useState(false);
  const queryClient = useQueryClient();

  const { data, isLoading, error } = useQuery({
    queryKey: ["portfolios"],
    queryFn: api.getPortfolios,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });

  // Set the first portfolio as default when portfolios are loaded
  useEffect(() => {
    if (data?.portfolios?.length && !selectedPortfolioId) {
      setSelectedPortfolioIdState(data.portfolios[0].id);
    }
  }, [data?.portfolios, selectedPortfolioId]);

  const setSelectedPortfolioId = useCallback(
    (id: string) => {
      setSelectedPortfolioIdState(id);
      // Invalidate queries that depend on the portfolio
      queryClient.invalidateQueries({ queryKey: ["portfolio"] });
      queryClient.invalidateQueries({ queryKey: ["score"] });
      queryClient.invalidateQueries({ queryKey: ["assets"] });
      // Clear documents when switching portfolios
      api.clearDocuments().catch(() => {});
    },
    [queryClient]
  );

  const createPortfolio = useCallback(
    async (name: string, assets: Asset[]): Promise<string> => {
      setIsCreating(true);
      try {
        const response = await api.createPortfolio({
          name,
          description: `Custom portfolio with ${assets.length} assets`,
          assets,
        });

        // Refresh the portfolios list
        await queryClient.invalidateQueries({ queryKey: ["portfolios"] });

        // Select the new portfolio
        setSelectedPortfolioIdState(response.portfolio.id);

        // Invalidate data queries for the new portfolio
        queryClient.invalidateQueries({ queryKey: ["portfolio"] });
        queryClient.invalidateQueries({ queryKey: ["score"] });
        queryClient.invalidateQueries({ queryKey: ["assets"] });

        // Clear documents for new portfolio
        api.clearDocuments().catch(() => {});

        return response.portfolio.id;
      } finally {
        setIsCreating(false);
      }
    },
    [queryClient]
  );

  const value: PortfolioContextType = {
    selectedPortfolioId,
    setSelectedPortfolioId,
    portfolios: data?.portfolios || [],
    isLoading,
    error: error as Error | null,
    createPortfolio,
    isCreating,
  };

  return (
    <PortfolioContext.Provider value={value}>
      {children}
    </PortfolioContext.Provider>
  );
}

export function usePortfolioContext() {
  const context = useContext(PortfolioContext);
  if (context === undefined) {
    throw new Error("usePortfolioContext must be used within a PortfolioProvider");
  }
  return context;
}
