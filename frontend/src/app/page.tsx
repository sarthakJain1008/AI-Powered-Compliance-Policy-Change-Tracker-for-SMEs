/**
 * @module RootPage
 * @description Root page — immediately redirects to /login.
 */

import { redirect } from 'next/navigation'

/**
 * Redirects the root URL to the login page.
 */
export default function RootPage() {
  redirect('/login')
}
