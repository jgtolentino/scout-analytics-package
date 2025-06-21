import React, { useState } from 'react';
import { useFilterStore } from '../stores/filterStore';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Calendar, MapPin, Package, Building, X, RotateCcw } from 'lucide-react';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';

const barangayOptions = [
  'Makati CBD', 'BGC', 'Ortigas', 'Quezon City', 'Manila', 'Pasig', 'Mandaluyong'
];

const storeOptions = [
  '7-Eleven Makati', 'SM Supermarket BGC', 'Robinsons Ortigas', 'Mercury Drug QC'
];

const categoryOptions = [
  'Beverages', 'Food & Snacks', 'Personal Care', 'Household Items', 'Others'
];

const brandOptions = [
  'Coca-Cola', 'Pepsi', 'Lucky Me', 'Nissin', 'Tide', 'Surf', 'San Miguel', 'Nestle'
];

export function GlobalFilterBar() {
  const {
    from,
    to,
    barangays,
    stores,
    categories,
    brands,
    setFilter,
    resetFilters,
  } = useFilterStore();

  const [showFilters, setShowFilters] = useState(false);

  const activeFilterCount = [
    from,
    to,
    ...barangays,
    ...stores,
    ...categories,
    ...brands,
  ].filter(Boolean).length;

  const removeArrayFilter = (key, value) => {
    const currentArray = useFilterStore.getState()[key];
    setFilter(key, currentArray.filter(item => item !== value));
  };

  return (
    <div className="border-b border-border bg-card">
      <div className="p-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <Button
              variant="outline"
              onClick={() => setShowFilters(!showFilters)}
              className="flex items-center space-x-2"
            >
              <span>Filters</span>
              {activeFilterCount > 0 && (
                <Badge variant="secondary" className="ml-2">
                  {activeFilterCount}
                </Badge>
              )}
            </Button>
            
            {activeFilterCount > 0 && (
              <Button
                variant="ghost"
                size="sm"
                onClick={resetFilters}
                className="flex items-center space-x-1"
              >
                <RotateCcw className="h-4 w-4" />
                <span>Reset</span>
              </Button>
            )}
          </div>
        </div>

        {/* Active Filters Display */}
        {activeFilterCount > 0 && (
          <div className="mt-3 flex flex-wrap gap-2">
            {from && (
              <Badge variant="outline" className="flex items-center space-x-1">
                <Calendar className="h-3 w-3" />
                <span>From: {from}</span>
                <X
                  className="h-3 w-3 cursor-pointer"
                  onClick={() => setFilter('from', '')}
                />
              </Badge>
            )}
            {to && (
              <Badge variant="outline" className="flex items-center space-x-1">
                <Calendar className="h-3 w-3" />
                <span>To: {to}</span>
                <X
                  className="h-3 w-3 cursor-pointer"
                  onClick={() => setFilter('to', '')}
                />
              </Badge>
            )}
            {barangays.map((barangay) => (
              <Badge key={barangay} variant="outline" className="flex items-center space-x-1">
                <MapPin className="h-3 w-3" />
                <span>{barangay}</span>
                <X
                  className="h-3 w-3 cursor-pointer"
                  onClick={() => removeArrayFilter('barangays', barangay)}
                />
              </Badge>
            ))}
            {stores.map((store) => (
              <Badge key={store} variant="outline" className="flex items-center space-x-1">
                <Building className="h-3 w-3" />
                <span>{store}</span>
                <X
                  className="h-3 w-3 cursor-pointer"
                  onClick={() => removeArrayFilter('stores', store)}
                />
              </Badge>
            ))}
            {categories.map((category) => (
              <Badge key={category} variant="outline" className="flex items-center space-x-1">
                <Package className="h-3 w-3" />
                <span>{category}</span>
                <X
                  className="h-3 w-3 cursor-pointer"
                  onClick={() => removeArrayFilter('categories', category)}
                />
              </Badge>
            ))}
            {brands.map((brand) => (
              <Badge key={brand} variant="outline" className="flex items-center space-x-1">
                <span>{brand}</span>
                <X
                  className="h-3 w-3 cursor-pointer"
                  onClick={() => removeArrayFilter('brands', brand)}
                />
              </Badge>
            ))}
          </div>
        )}

        {/* Filter Controls */}
        {showFilters && (
          <div className="mt-4 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 p-4 bg-muted/20 rounded-lg">
            <div className="space-y-2">
              <label className="text-sm font-medium">Date From</label>
              <Input
                type="date"
                value={from}
                onChange={(e) => setFilter('from', e.target.value)}
              />
            </div>
            
            <div className="space-y-2">
              <label className="text-sm font-medium">Date To</label>
              <Input
                type="date"
                value={to}
                onChange={(e) => setFilter('to', e.target.value)}
              />
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium">Barangay</label>
              <Select
                onValueChange={(value) => {
                  if (!barangays.includes(value)) {
                    setFilter('barangays', [...barangays, value]);
                  }
                }}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select barangay" />
                </SelectTrigger>
                <SelectContent>
                  {barangayOptions.map((option) => (
                    <SelectItem key={option} value={option}>
                      {option}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium">Store</label>
              <Select
                onValueChange={(value) => {
                  if (!stores.includes(value)) {
                    setFilter('stores', [...stores, value]);
                  }
                }}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select store" />
                </SelectTrigger>
                <SelectContent>
                  {storeOptions.map((option) => (
                    <SelectItem key={option} value={option}>
                      {option}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium">Category</label>
              <Select
                onValueChange={(value) => {
                  if (!categories.includes(value)) {
                    setFilter('categories', [...categories, value]);
                  }
                }}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select category" />
                </SelectTrigger>
                <SelectContent>
                  {categoryOptions.map((option) => (
                    <SelectItem key={option} value={option}>
                      {option}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium">Brand</label>
              <Select
                onValueChange={(value) => {
                  if (!brands.includes(value)) {
                    setFilter('brands', [...brands, value]);
                  }
                }}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select brand" />
                </SelectTrigger>
                <SelectContent>
                  {brandOptions.map((option) => (
                    <SelectItem key={option} value={option}>
                      {option}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

