//helper function for pages
import {SiteConfig} from '@my/config/dist/AppConfig'
export * from '../components/AdminPage'
import { NextPageContext } from 'next'
import {API} from 'protobase'
import {withSession, getURLWithToken} from './Session'

export const SSR = (fn) => SiteConfig.SSR ? fn : undefined

export function DataSSR(sourceUrl, permissions?:string[]|any[]|null, props={}) {
    return SSR(async (context:NextPageContext) => {
        return withSession(context, permissions, {
          pageState: {
            sourceUrl,
            initialItems: await API.get({url: sourceUrl, ...props}),
            ...props,
          }
        })
    })
}

export function PaginatedData(sourceUrl: string|Function, permissions?:string[]|any[]|null, extraData?:{[key: string]: string}) {
  return PaginatedDataSSR(sourceUrl, permissions, {}, async (context) => {
    // const objects = await API.get(getURLWithToken(objectsSourceUrl, context))
    // return {
    //   objects: objects.isLoaded ? objects.data.items : []
    // }
    if(!extraData) return {}
    const result = {}
    for (const key of Object.keys(extraData)) {
      result[key] = await API.get(getURLWithToken(extraData[key], context))
    }
    return result
  })
}

export function PaginatedDataSSR(sourceUrl: string|Function, permissions?:string[]|any[]|null, dataProps:any={}, extraData:any={}) {
  return SSR(async (context:NextPageContext) => {
    const filters = Object.keys(context.query ?? {}).filter(q => q.startsWith('filter')).reduce((total, current: string) => ({
      ...total,
      [current]: context.query[current]
    }), {}) ?? {}

    const _dataProps = {
      ...filters,
      itemsPerPage: parseInt(context.query.itemsPerPage as string) ? parseInt(context.query.itemsPerPage as string) : '',
      page: parseInt(context.query.page as string, 10) ? parseInt(context.query.page as string, 10) : '',
      search: context.query.search ?? '',
      orderBy: context.query.orderBy ?? '',
      orderDirection: context.query.orderDirection ?? '',
      view: context.query.view?? '',
      item: context.query.item?? '',
      editFile: context.query.editFile??'',
      ...(typeof dataProps === "function"? await dataProps(context) : dataProps),
    }
    const _sourceUrl = typeof sourceUrl === 'function' ? sourceUrl(context) : sourceUrl

    return withSession(context, permissions, {
      sourceUrl: _sourceUrl,
      initialItems: await API.get({url: getURLWithToken(_sourceUrl, context), ..._dataProps}),
      itemData: context.query.item ? await API.get(getURLWithToken(_sourceUrl+'/'+context.query.item, context)) : '',
      extraData: {...(typeof extraData === "function"? await extraData(context) : extraData)},
      pageState: {
        ..._dataProps,
      }
    })
  })
}