import { createContext, useContext, useState, useCallback, useEffect, type ReactNode } from "react";
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
  deletePortfolio: (portfolioId: string) => Promise<void>;
  isDeleting: boolean;
}

const PortfolioContext = createContext<PortfolioContextType | undefined>(undefined);

interface PortfolioProviderProps {
  children: ReactNode;
}

export function PortfolioProvider({ children }: PortfolioProviderProps) {
  const [selectedPortfolioId, setSelectedPortfolioIdState] = useState<string | undefined>(undefined);
  const [isCreating, setIsCreating] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);
  const queryClient = useQueryClient();

  const { data, isLoading, error } = useQuery({
    queryKey: ["portfolios"],
    queryFn: api.getPortfolios,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });

  // Auto-select the first portfolio when the list loads
  useEffect(() => {
    if (data?.portfolios?.length && !selectedPortfolioId) {
      setSelectedPortfolioIdState(data.portfolios[0].id);
    }
  }, [data?.portfolios, selectedPortfolioId]);

  const setSelectedPortfolioId = useCallback(
    (id: string) => {
      setSelectedPortfolioIdState(id);
      queryClient.invalidateQueries({ queryKey: ["portfolio"] });
      queryClient.invalidateQueries({ queryKey: ["score"] });
      queryClient.invalidateQueries({ queryKey: ["assets"] });
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

        await queryClient.invalidateQueries({ queryKey: ["portfolios"] });
        setSelectedPortfolioIdState(response.portfolio.id);
        queryClient.invalidateQueries({ queryKey: ["portfolio"] });
        queryClient.invalidateQueries({ queryKey: ["score"] });
        queryClient.invalidateQueries({ queryKey: ["assets"] });
        api.clearDocuments().catch(() => {});

        return response.portfolio.id;
      } finally {
        setIsCreating(false);
      }
    },
    [queryClient]
  );

  const deletePortfolio = useCallback(
    async (portfolioId: string): Promise<void> => {
      setIsDeleting(true);
      try {
        await api.deletePortfolio(portfolioId);

        // Refresh portfolios list
        await queryClient.invalidateQueries({ queryKey: ["portfolios"] });

        // If the deleted portfolio was the selected one, switch to the first remaining
        if (portfolioId === selectedPortfolioId) {
          const remaining = data?.portfolios?.filter((p) => p.id !== portfolioId) ?? [];
          const nextId = remaining[0]?.id;
          setSelectedPortfolioIdState(nextId);
          queryClient.invalidateQueries({ queryKey: ["portfolio"] });
          queryClient.invalidateQueries({ queryKey: ["score"] });
          queryClient.invalidateQueries({ queryKey: ["assets"] });
        }
      } finally {
        setIsDeleting(false);
      }
    },
    [queryClient, selectedPortfolioId, data?.portfolios]
  );

  const value: PortfolioContextType = {
    selectedPortfolioId,
    setSelectedPortfolioId,
    portfolios: data?.portfolios ?? [],
    isLoading,
    error: error as Error | null,
    createPortfolio,
    isCreating,
    deletePortfolio,
    isDeleting,
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
