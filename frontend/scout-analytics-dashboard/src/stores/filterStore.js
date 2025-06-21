import { create } from 'zustand';
import { persist } from 'zustand/middleware';

const defaultFilters = {
  from: '',
  to: '',
  barangays: [],
  stores: [],
  categories: [],
  brands: [],
};

export const useFilterStore = create(
  persist(
    (set, get) => ({
      ...defaultFilters,
      
      setFilter: (key, value) => {
        set((state) => ({
          ...state,
          [key]: value,
        }));
        
        // Update URL
        const queryString = get().getQueryString();
        const url = new URL(window.location.href);
        url.search = queryString;
        window.history.replaceState({}, '', url.toString());
      },
      
      resetFilters: () => {
        set(defaultFilters);
        
        // Clear URL params
        const url = new URL(window.location.href);
        url.search = '';
        window.history.replaceState({}, '', url.toString());
      },
      
      getQueryString: () => {
        const state = get();
        const params = new URLSearchParams();
        
        if (state.from) params.set('from', state.from);
        if (state.to) params.set('to', state.to);
        if (state.barangays.length > 0) params.set('barangays', state.barangays.join(','));
        if (state.stores.length > 0) params.set('stores', state.stores.join(','));
        if (state.categories.length > 0) params.set('categories', state.categories.join(','));
        if (state.brands.length > 0) params.set('brands', state.brands.join(','));
        if (state.hour) params.set('hour', state.hour);
        if (state.gender) params.set('gender', state.gender);
        
        return params.toString();
      },
      
      setFromQueryString: (queryString) => {
        const params = new URLSearchParams(queryString);
        
        set({
          from: params.get('from') || '',
          to: params.get('to') || '',
          barangays: params.get('barangays')?.split(',').filter(Boolean) || [],
          stores: params.get('stores')?.split(',').filter(Boolean) || [],
          categories: params.get('categories')?.split(',').filter(Boolean) || [],
          brands: params.get('brands')?.split(',').filter(Boolean) || [],
          hour: params.get('hour') || undefined,
          gender: params.get('gender') || undefined,
        });
      },
    }),
    {
      name: 'scout-analytics-filters',
      partialize: (state) => ({
        from: state.from,
        to: state.to,
        barangays: state.barangays,
        stores: state.stores,
        categories: state.categories,
        brands: state.brands,
        hour: state.hour,
        gender: state.gender,
      }),
    }
  )
);

